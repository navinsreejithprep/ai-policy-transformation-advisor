# Agent Design

Every agent is defined in `app/agents/definitions.py` (role/goal/backstory) and given a task built in
`app/crew/tasks.py`. Every task except the Synthesis Advisor's sets `output_pydantic=<Model>`, so CrewAI
constrains and validates the agent's output against the schema in `app/models/schemas.py` before the
runner ever sees it.

## 1. Policy Analyst

- **Input**: raw policy text (untrusted user input — see Prompt Injection below)
- **Output**: `PolicyAnalysis` — objectives, target beneficiaries, mechanisms, implementation
  requirements, expected outcomes, and a list of `PolicyAssumption` (each flagged
  `is_evidence_backed: bool`)
- **Downstream use**: `.objectives` and `.assumptions` become the retrieval queries for the Evidence
  Analyst — this is the "genuine hand-off" the spec asked for: the Evidence Analyst doesn't see the raw
  policy text fresh, it sees *this agent's interpretation* of what needs evidence.

## 2. Evidence Analyst

- **Input**: `PolicyAnalysis` (as raw JSON) + retrieved passages from ChromaDB, each tagged
  `[document_name, page N]` and `[DEMO DATA]` where applicable
- **Output**: `EvidenceReport` — a list of `EvidenceFinding` (claim, evidence, `sources: SourceCitation[]`,
  confidence, optional contradiction) plus `evidence_gaps: list[str]`
- **Grounding rule**: explicitly instructed that every `sources` entry must reference a document/page
  that actually appears in the supplied context, and to use `evidence_gaps` rather than force a citation
  when nothing relevant was retrieved.

## 3. Stakeholder Analyst

- **Input**: Policy analysis + evidence findings
- **Output**: `StakeholderMatrix` — each `Stakeholder` has `influence` and `interest_level`
  (`High`/`Medium`/`Low`, used to place them on the influence-interest matrix in the UI), free-text
  `interest`/`role`/`likely_concerns`/`required_engagement`, and `is_inference: bool` (defaults `True` —
  the agent must actively justify setting it `False`).

## 4. Risk Analyst

- **Input**: policy + evidence + stakeholder context
- **Output**: `RiskRegister` — `Risk` objects across 8 fixed categories (`RiskCategory` enum: Strategic,
  Operational, Financial, Regulatory, Technology, Data, Adoption, Execution), each with qualitative
  `likelihood`/`impact`, optional `evidence`, `mitigation`, `owner`. The register carries a fixed `note`
  stating these are qualitative judgements, not measured probabilities.

## 5. Benchmark Analyst

- **Input**: policy analysis + a *separate* retrieval pass framed around "comparable programme
  benchmark for: {objective}" (not the same context as the Evidence Analyst — this deliberately biases
  retrieval toward comparison-shaped passages like the Estlandia case study)
- **Output**: `BenchmarkReport` — each `Benchmark` has a
  `comparability_supported_by_evidence: bool` the agent must justify, and `sources`.

## 6. Implementation Strategist

- **Input**: the full prior context (policy + evidence + stakeholders + risks + benchmarks)
- **Output**: `ImplementationPlan` — `NinetyDayPlan` (days 0-30/31-60/61-90) + `TwelveMonthRoadmap`
  (Q1-Q4), each made of `RoadmapItem`s with a **required** `linked_to` field naming the specific risk,
  stakeholder concern or evidence gap the action responds to. This is the mechanism that prevents
  "recommendations that come from nowhere."

## 7. Independent Challenge Reviewer

- **Input**: the full analysis (all six upstream outputs' raw JSON)
- **Output**: `ReviewResult` — `verdict: PASS | NEEDS_REVISION` + a list of `ReviewIssue` (each naming a
  `target_agent` and severity). This agent's backstory explicitly frames it as *not* trying to be
  agreeable — its only goal is finding fault.
- **What happens on NEEDS_REVISION**: `app/crew/runner.py` groups issues by (normalized) `target_agent`,
  re-executes exactly those agents' tasks with the reviewer's feedback appended to their original
  context, then re-runs the reviewer. Bounded to `REVISION_MAX_CYCLES` (default 2) — see
  `docs/architecture.md` for why this is application-level control flow rather than a CrewAI-native loop.

## Synthesis Advisor (not part of the original 7, added to fix a real bug)

- **Input**: the full, possibly-revised final context
- **Output**: plain text, max 500 words — no `output_pydantic`, deliberately, because its only job is
  compression/framing of facts that already exist, not generating new structured claims.
- Everything else in the final report (evidence table, risk register, roadmap, sources, etc.) is
  assembled in Python from the upstream Pydantic objects, not regenerated here.

## Prompt injection awareness

The Policy Analyst is the only agent that sees raw, untrusted user text verbatim. Its task description
includes an explicit instruction (`PROMPT_INJECTION_GUARD` in `app/crew/tasks.py`) to treat that text as
data to analyze, not instructions to follow, and to disregard any embedded attempt to change its role or
reveal system prompts. This is a mitigation, not a guarantee — see the Interview Guide for how to discuss
its limits honestly.
