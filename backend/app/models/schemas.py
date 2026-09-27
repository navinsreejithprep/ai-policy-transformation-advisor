"""Structured contracts exchanged between agents, the crew runner and the API.

Every agent that can produce one of these models is given `output_pydantic=<Model>`
so CrewAI forces (and validates) structured JSON instead of free-form prose. This is
what lets the final report be assembled deterministically in code (see
app/crew/synthesis.py) instead of trusting a single LLM call to not drop or
hallucinate a section.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class DocumentCategory(str, Enum):
    """Purely informational tagging to help a user know what's *useful* to add to
    the knowledge base — never enforced or required (a document with no category
    still ingests and retrieves normally)."""

    POLICY = "policy"
    EVIDENCE = "evidence"
    BENCHMARK = "benchmark"
    RISK = "risk"
    STAKEHOLDER = "stakeholder"
    BUDGET = "budget"
    OTHER = "other"


class ConfidenceLevel(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class ImpactLevel(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class ClaimType(str, Enum):
    """Every important statement in the final report is tagged with one of these
    so a reader can tell fact from opinion at a glance (spec requirement)."""

    SOURCE_BACKED_FACT = "source_backed_fact"
    ANALYSIS = "analysis"
    RECOMMENDATION = "recommendation"
    ASSUMPTION = "assumption"
    UNCERTAIN = "uncertain"


class SourceCitation(BaseModel):
    document_name: str
    page_number: Optional[int] = None
    section: Optional[str] = None
    chunk_id: Optional[str] = None
    is_demo_data: bool = False
    passage_preview: Optional[str] = Field(
        default=None, description="The retrieved passage text, populated only when built from a real retrieval hit"
    )

    def label(self) -> str:
        loc = f", p. {self.page_number}" if self.page_number else ""
        sec = f" ({self.section})" if self.section else ""
        return f"{self.document_name}{loc}{sec}"


# ---------------------------------------------------------------------------
# Agent 1 — Policy Analyst
# ---------------------------------------------------------------------------

class PolicyAssumption(BaseModel):
    assumption: str
    is_evidence_backed: bool = False


class PolicyAnalysis(BaseModel):
    objectives: list[str] = Field(default_factory=list)
    target_beneficiaries: list[str] = Field(default_factory=list)
    mechanisms: list[str] = Field(default_factory=list)
    implementation_requirements: list[str] = Field(default_factory=list)
    expected_outcomes: list[str] = Field(default_factory=list)
    assumptions: list[PolicyAssumption] = Field(default_factory=list)
    summary: str = ""


# ---------------------------------------------------------------------------
# Agent 2 — Evidence Analyst
# ---------------------------------------------------------------------------

class EvidenceFinding(BaseModel):
    claim: str
    evidence: str
    sources: list[SourceCitation] = Field(default_factory=list)
    confidence: ConfidenceLevel = ConfidenceLevel.LOW
    contradiction: Optional[str] = None


class EvidenceReport(BaseModel):
    findings: list[EvidenceFinding] = Field(default_factory=list)
    evidence_gaps: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Agent 3 — Stakeholder Analyst
# ---------------------------------------------------------------------------

class Stakeholder(BaseModel):
    name: str
    category: str
    role: str
    interest: str
    interest_level: ImpactLevel = Field(description="How much this stakeholder cares about the outcome, for the influence-interest matrix")
    influence: ImpactLevel
    likely_concerns: list[str] = Field(default_factory=list)
    required_engagement: str
    is_inference: bool = True


class StakeholderMatrix(BaseModel):
    stakeholders: list[Stakeholder] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Agent 4 — Risk Analyst
# ---------------------------------------------------------------------------

class RiskCategory(str, Enum):
    STRATEGIC = "Strategic"
    OPERATIONAL = "Operational"
    FINANCIAL = "Financial"
    REGULATORY = "Regulatory"
    TECHNOLOGY = "Technology"
    DATA = "Data"
    ADOPTION = "Adoption"
    EXECUTION = "Execution"


class Risk(BaseModel):
    category: RiskCategory
    description: str
    likelihood: ImpactLevel
    impact: ImpactLevel
    evidence: Optional[str] = None
    mitigation: str
    owner: str


class RiskRegister(BaseModel):
    risks: list[Risk] = Field(default_factory=list)
    note: str = "Likelihood and impact are qualitative analytical judgements, not measured probabilities."


# ---------------------------------------------------------------------------
# Agent 5 — Benchmark Analyst
# ---------------------------------------------------------------------------

class Benchmark(BaseModel):
    name: str
    objective: str
    approach: str
    implementation_model: str
    funding: Optional[str] = None
    governance: Optional[str] = None
    outcomes: Optional[str] = None
    lessons: list[str] = Field(default_factory=list)
    comparability_supported_by_evidence: bool = False
    sources: list[SourceCitation] = Field(default_factory=list)


class BenchmarkReport(BaseModel):
    benchmarks: list[Benchmark] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Agent 6 — Implementation Strategist
# ---------------------------------------------------------------------------

class RoadmapItem(BaseModel):
    workstream: str
    action: str
    owner: str
    dependency: Optional[str] = None
    kpi: str
    expected_outcome: str
    linked_to: Optional[str] = Field(
        default=None, description="Which risk, stakeholder issue or evidence gap this action responds to"
    )


class NinetyDayPlan(BaseModel):
    days_0_30: list[RoadmapItem] = Field(default_factory=list)
    days_31_60: list[RoadmapItem] = Field(default_factory=list)
    days_61_90: list[RoadmapItem] = Field(default_factory=list)


class TwelveMonthRoadmap(BaseModel):
    quarter_1: list[RoadmapItem] = Field(default_factory=list)
    quarter_2: list[RoadmapItem] = Field(default_factory=list)
    quarter_3: list[RoadmapItem] = Field(default_factory=list)
    quarter_4: list[RoadmapItem] = Field(default_factory=list)


class KPI(BaseModel):
    name: str
    target: str
    workstream: str


class ImplementationPlan(BaseModel):
    ninety_day_plan: NinetyDayPlan
    twelve_month_roadmap: TwelveMonthRoadmap
    governance_model: str
    kpis: list[KPI] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Agent 7 — Challenge / Review Agent
# ---------------------------------------------------------------------------

class ReviewVerdict(str, Enum):
    PASS = "PASS"
    NEEDS_REVISION = "NEEDS_REVISION"


class ReviewIssue(BaseModel):
    target_agent: str = Field(description="Which upstream agent's output this issue relates to, e.g. 'risk', 'stakeholder'")
    issue: str
    severity: ImpactLevel


class ReviewResult(BaseModel):
    verdict: ReviewVerdict
    issues: list[ReviewIssue] = Field(default_factory=list)
    summary: str = ""


# ---------------------------------------------------------------------------
# Final synthesis
# ---------------------------------------------------------------------------

class RevisionLogEntry(BaseModel):
    cycle: int
    verdict: ReviewVerdict
    issues_raised: int
    agents_revised: list[str] = Field(default_factory=list)


class FinalReport(BaseModel):
    executive_summary: str
    policy_analysis: PolicyAnalysis
    evidence: EvidenceReport
    stakeholders: StakeholderMatrix
    risks: RiskRegister
    benchmarks: BenchmarkReport
    implementation: ImplementationPlan
    review: ReviewResult
    revision_log: list[RevisionLogEntry] = Field(default_factory=list)
    evidence_gaps: list[str] = Field(default_factory=list)
    key_assumptions: list[str] = Field(default_factory=list)
    sources: list[SourceCitation] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    disclaimer: str = (
        "AI-generated analysis — verify critical decisions against primary sources. "
        "This is a portfolio proof-of-concept; do not treat outputs as production-grade advice."
    )


# ---------------------------------------------------------------------------
# Job / API-facing models
# ---------------------------------------------------------------------------

class AnalysisStage(str, Enum):
    QUEUED = "queued"
    POLICY_ANALYSIS = "policy_analysis"
    EVIDENCE_RESEARCH = "evidence_research"
    STAKEHOLDER_ANALYSIS = "stakeholder_analysis"
    RISK_ASSESSMENT = "risk_assessment"
    BENCHMARKING = "benchmarking"
    IMPLEMENTATION_PLANNING = "implementation_planning"
    INDEPENDENT_REVIEW = "independent_review"
    REVISION = "revision"
    SYNTHESIS = "synthesis"
    COMPLETE = "complete"
    FAILED = "failed"


class AnalysisJobStatus(BaseModel):
    job_id: str
    stage: AnalysisStage
    progress_pct: int = 0
    error: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class AnalysisStartRequest(BaseModel):
    policy_text: str = Field(min_length=20, max_length=20000)


class AnalysisStartResponse(BaseModel):
    job_id: str
    status: AnalysisStage


class DocumentInfo(BaseModel):
    document_name: str
    chunks: int
    pages: int
    is_demo_data: bool
    category: DocumentCategory = DocumentCategory.OTHER
    status: str = "indexed"


class DocumentListResponse(BaseModel):
    documents: list[DocumentInfo]
    total_chunks: int
    last_indexed_at: Optional[datetime] = None
