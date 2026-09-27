"""Orchestrates the 7-agent pipeline + independent review + bounded revision loop
+ deterministic synthesis into a FinalReport.

See app/crew/tasks.py for why this is manual step-by-step orchestration rather
than a single CrewAI Crew.kickoff() call.
"""
import time
from typing import Callable, Optional

from ..agents.definitions import make_agents
from ..config import settings
from ..models.schemas import (
    AnalysisStage,
    BenchmarkReport,
    EvidenceReport,
    FinalReport,
    ImplementationPlan,
    PolicyAnalysis,
    ReviewResult,
    ReviewVerdict,
    RevisionLogEntry,
    RiskRegister,
    SourceCitation,
    StakeholderMatrix,
)
from ..rag.retrieve import retrieve_evidence, rows_to_citations
from ..utils.logging import get_logger, truncate
from . import tasks as T

logger = get_logger(__name__)

ProgressCallback = Optional[Callable[[AnalysisStage], None]]


class AnalysisError(Exception):
    """Raised when the pipeline cannot produce a report (LLM failure, malformed
    output that survived retries, etc). Callers must not fabricate a report when
    this is raised."""


def _run(task, agent, step_name: str):
    """Execute a single pre-built Task (context is already embedded in its
    description by app/crew/tasks.py builders)."""
    start = time.monotonic()
    try:
        output = task.execute_sync(agent=agent)
    except Exception as exc:  # LLM/API failure, timeout, network error
        logger.error("step failed step=%s error=%s", step_name, exc)
        raise AnalysisError(f"'{step_name}' failed: {exc}") from exc
    elapsed = time.monotonic() - start
    logger.info("step complete step=%s latency_s=%.1f", step_name, elapsed)
    if task.output_pydantic and output.pydantic is None:
        raise AnalysisError(f"'{step_name}' returned malformed output that could not be parsed.")
    return output


def _build_evidence_context(queries: list[str], top_k: int = None) -> tuple[str, list[dict]]:
    seen_ids = set()
    all_rows = []
    parts = []
    for q in queries:
        rows = retrieve_evidence(q, top_k=top_k or settings.top_k_default)
        for r in rows:
            cid = r["metadata"].get("chunk_id")
            if cid in seen_ids:
                continue
            seen_ids.add(cid)
            all_rows.append(r)
            demo_tag = " [DEMO DATA]" if r["metadata"].get("is_demo_data") else ""
            parts.append(f"[{r['document']}, page {r['page']}]{demo_tag} {r['text']}")
    if not parts:
        return "No matching evidence was found in the knowledge base for these queries.", []
    return "\n\n".join(parts), all_rows


def run_analysis_pipeline(policy_text: str, on_stage: ProgressCallback = None) -> FinalReport:
    def stage(s: AnalysisStage):
        logger.info("stage=%s", s.value)
        if on_stage:
            on_stage(s)

    agents = make_agents()
    logger.info("analysis started policy_text=%s", truncate(policy_text))

    # 1. Policy analysis -------------------------------------------------
    stage(AnalysisStage.POLICY_ANALYSIS)
    policy_task = T.build_policy_task(policy_text)
    policy_output = _run(policy_task, agents["policy"], "policy_analysis")
    policy_analysis: PolicyAnalysis = policy_output.pydantic
    policy_ctx = policy_output.raw

    # 2. Evidence research -------------------------------------------------
    stage(AnalysisStage.EVIDENCE_RESEARCH)
    evidence_queries = (policy_analysis.objectives or [policy_text[:200]]) + [
        a.assumption for a in policy_analysis.assumptions
    ]
    evidence_ctx_text, evidence_rows = _build_evidence_context(evidence_queries[:8])
    evidence_task = T.build_evidence_task(policy_ctx, evidence_ctx_text)
    evidence_output = _run(evidence_task, agents["evidence"], "evidence_research")
    evidence_report: EvidenceReport = evidence_output.pydantic
    evidence_ctx = evidence_output.raw

    # 3. Stakeholder analysis -----------------------------------------------
    stage(AnalysisStage.STAKEHOLDER_ANALYSIS)
    stakeholder_task = T.build_stakeholder_task(policy_ctx, evidence_ctx)
    stakeholder_output = _run(stakeholder_task, agents["stakeholder"], "stakeholder_analysis")
    stakeholder_matrix: StakeholderMatrix = stakeholder_output.pydantic
    stakeholder_ctx = stakeholder_output.raw

    # 4. Risk analysis -------------------------------------------------------
    stage(AnalysisStage.RISK_ASSESSMENT)
    risk_task = T.build_risk_task(policy_ctx, evidence_ctx, stakeholder_ctx)
    risk_output = _run(risk_task, agents["risk"], "risk_assessment")
    risk_register: RiskRegister = risk_output.pydantic

    # 5. Benchmarking ---------------------------------------------------------
    stage(AnalysisStage.BENCHMARKING)
    benchmark_ctx_text, benchmark_rows = _build_evidence_context(
        [f"comparable programme benchmark for: {o}" for o in policy_analysis.objectives[:5]] or [policy_text[:200]]
    )
    benchmark_task = T.build_benchmark_task(policy_ctx, benchmark_ctx_text)
    benchmark_output = _run(benchmark_task, agents["benchmark"], "benchmarking")
    benchmark_report: BenchmarkReport = benchmark_output.pydantic

    # 6. Implementation planning ----------------------------------------------
    stage(AnalysisStage.IMPLEMENTATION_PLANNING)
    full_context_for_impl = (
        f"POLICY:\n{policy_ctx}\n\nEVIDENCE:\n{evidence_ctx}\n\n"
        f"STAKEHOLDERS:\n{stakeholder_ctx}\n\nRISKS:\n{risk_output.raw}\n\nBENCHMARKS:\n{benchmark_output.raw}"
    )
    implementation_task = T.build_implementation_task(full_context_for_impl)
    implementation_output = _run(implementation_task, agents["implementation"], "implementation_planning")
    implementation_plan: ImplementationPlan = implementation_output.pydantic

    # State that the revision loop mutates.
    state = {
        "policy": (policy_analysis, policy_output.raw),
        "evidence": (evidence_report, evidence_output.raw),
        "stakeholder": (stakeholder_matrix, stakeholder_output.raw),
        "risk": (risk_register, risk_output.raw),
        "benchmark": (benchmark_report, benchmark_output.raw),
        "implementation": (implementation_plan, implementation_output.raw),
    }

    def full_context() -> str:
        return "\n\n".join(f"{k.upper()}:\n{v[1]}" for k, v in state.items())

    # 7. Independent review + bounded revision loop ----------------------------
    stage(AnalysisStage.INDEPENDENT_REVIEW)
    review_task = T.build_review_task(full_context())
    review_output = _run(review_task, agents["reviewer"], "independent_review")
    review: ReviewResult = review_output.pydantic

    revision_log: list[RevisionLogEntry] = []
    cycle = 0
    while review.verdict == ReviewVerdict.NEEDS_REVISION and cycle < settings.revision_max_cycles:
        cycle += 1
        stage(AnalysisStage.REVISION)
        revised_agents = []

        def _normalize(name: str) -> str:
            name = name.strip().lower()
            for key in state:
                if key in name:
                    return key
            return name

        normalized_issues = [(_normalize(i.target_agent), i) for i in review.issues]
        # De-dupe target agents so we revise each flagged agent once per cycle.
        targets = {key for key, _ in normalized_issues if key in state}
        for target in targets:
            _, raw = state[target]
            feedback = "\n".join(
                f"- {i.issue} (severity: {i.severity.value})" for key, i in normalized_issues if key == target
            )
            try:
                revision_task = T.build_revision_task(target, raw, feedback)
                revised_output = _run(revision_task, agents[target], f"revision_{target}_cycle{cycle}")
                state[target] = (revised_output.pydantic, revised_output.raw)
                revised_agents.append(target)
            except AnalysisError as exc:
                logger.warning("revision skipped target=%s error=%s", target, exc)

        stage(AnalysisStage.INDEPENDENT_REVIEW)
        review_task = T.build_review_task(full_context())
        review_output = _run(review_task, agents["reviewer"], f"independent_review_cycle{cycle}")
        review = review_output.pydantic
        revision_log.append(
            RevisionLogEntry(
                cycle=cycle,
                verdict=review.verdict,
                issues_raised=len(review.issues),
                agents_revised=revised_agents,
            )
        )

    policy_analysis = state["policy"][0]
    evidence_report = state["evidence"][0]
    stakeholder_matrix = state["stakeholder"][0]
    risk_register = state["risk"][0]
    benchmark_report = state["benchmark"][0]
    implementation_plan = state["implementation"][0]

    # 8. Deterministic synthesis --------------------------------------------
    # Everything except the executive summary is assembled here in code from the
    # structured agent outputs above — not re-generated by an LLM — so nothing in
    # the final report can be hallucinated at this stage.
    stage(AnalysisStage.SYNTHESIS)
    synthesis_task = T.build_synthesis_task(full_context())
    synthesis_output = _run(synthesis_task, agents["synthesis"], "synthesis")
    executive_summary = synthesis_output.raw

    all_citations: list[SourceCitation] = []
    seen = set()
    for finding in evidence_report.findings:
        for c in finding.sources:
            key = (c.document_name, c.page_number)
            if key not in seen:
                seen.add(key)
                all_citations.append(c)
    for row in evidence_rows + benchmark_rows:
        c = rows_to_citations([row])[0]
        key = (c.document_name, c.page_number)
        if key not in seen:
            seen.add(key)
            all_citations.append(c)

    report = FinalReport(
        executive_summary=executive_summary,
        policy_analysis=policy_analysis,
        evidence=evidence_report,
        stakeholders=stakeholder_matrix,
        risks=risk_register,
        benchmarks=benchmark_report,
        implementation=implementation_plan,
        review=review,
        revision_log=revision_log,
        evidence_gaps=evidence_report.evidence_gaps,
        key_assumptions=[a.assumption for a in policy_analysis.assumptions],
        sources=all_citations,
    )
    stage(AnalysisStage.COMPLETE)
    logger.info(
        "analysis complete verdict=%s revision_cycles=%d sources=%d",
        review.verdict.value,
        len(revision_log),
        len(all_citations),
    )
    return report
