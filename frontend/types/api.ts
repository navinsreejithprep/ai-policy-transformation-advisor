// Mirrors backend/app/models/schemas.py. Keep these in sync manually — this is a
// POC without a shared schema generator (a production version would generate
// this file from the FastAPI OpenAPI schema).

export type Level = "High" | "Medium" | "Low";

export type DocumentCategory = "policy" | "evidence" | "benchmark" | "risk" | "stakeholder" | "budget" | "other";

export interface SourceCitation {
  document_name: string;
  page_number: number | null;
  section: string | null;
  chunk_id: string | null;
  is_demo_data: boolean;
  passage_preview: string | null;
}

export interface PolicyAssumption {
  assumption: string;
  is_evidence_backed: boolean;
}

export interface PolicyAnalysis {
  objectives: string[];
  target_beneficiaries: string[];
  mechanisms: string[];
  implementation_requirements: string[];
  expected_outcomes: string[];
  assumptions: PolicyAssumption[];
  summary: string;
}

export interface EvidenceFinding {
  claim: string;
  evidence: string;
  sources: SourceCitation[];
  confidence: Level;
  contradiction: string | null;
}

export interface EvidenceReport {
  findings: EvidenceFinding[];
  evidence_gaps: string[];
}

export interface Stakeholder {
  name: string;
  category: string;
  role: string;
  interest: string;
  interest_level: Level;
  influence: Level;
  likely_concerns: string[];
  required_engagement: string;
  is_inference: boolean;
}

export interface StakeholderMatrix {
  stakeholders: Stakeholder[];
}

export type RiskCategory =
  | "Strategic"
  | "Operational"
  | "Financial"
  | "Regulatory"
  | "Technology"
  | "Data"
  | "Adoption"
  | "Execution";

export interface Risk {
  category: RiskCategory;
  description: string;
  likelihood: Level;
  impact: Level;
  evidence: string | null;
  mitigation: string;
  owner: string;
}

export interface RiskRegister {
  risks: Risk[];
  note: string;
}

export interface Benchmark {
  name: string;
  objective: string;
  approach: string;
  implementation_model: string;
  funding: string | null;
  governance: string | null;
  outcomes: string | null;
  lessons: string[];
  comparability_supported_by_evidence: boolean;
  sources: SourceCitation[];
}

export interface BenchmarkReport {
  benchmarks: Benchmark[];
}

export interface RoadmapItem {
  workstream: string;
  action: string;
  owner: string;
  dependency: string | null;
  kpi: string;
  expected_outcome: string;
  linked_to: string | null;
}

export interface NinetyDayPlan {
  days_0_30: RoadmapItem[];
  days_31_60: RoadmapItem[];
  days_61_90: RoadmapItem[];
}

export interface TwelveMonthRoadmap {
  quarter_1: RoadmapItem[];
  quarter_2: RoadmapItem[];
  quarter_3: RoadmapItem[];
  quarter_4: RoadmapItem[];
}

export interface KPI {
  name: string;
  target: string;
  workstream: string;
}

export interface ImplementationPlan {
  ninety_day_plan: NinetyDayPlan;
  twelve_month_roadmap: TwelveMonthRoadmap;
  governance_model: string;
  kpis: KPI[];
}

export type ReviewVerdict = "PASS" | "NEEDS_REVISION";

export interface ReviewIssue {
  target_agent: string;
  issue: string;
  severity: Level;
}

export interface ReviewResult {
  verdict: ReviewVerdict;
  issues: ReviewIssue[];
  summary: string;
}

export interface RevisionLogEntry {
  cycle: number;
  verdict: ReviewVerdict;
  issues_raised: number;
  agents_revised: string[];
}

export interface FinalReport {
  executive_summary: string;
  policy_analysis: PolicyAnalysis;
  evidence: EvidenceReport;
  stakeholders: StakeholderMatrix;
  risks: RiskRegister;
  benchmarks: BenchmarkReport;
  implementation: ImplementationPlan;
  review: ReviewResult;
  revision_log: RevisionLogEntry[];
  evidence_gaps: string[];
  key_assumptions: string[];
  sources: SourceCitation[];
  generated_at: string;
  disclaimer: string;
}

export type AnalysisStage =
  | "queued"
  | "policy_analysis"
  | "evidence_research"
  | "stakeholder_analysis"
  | "risk_assessment"
  | "benchmarking"
  | "implementation_planning"
  | "independent_review"
  | "revision"
  | "synthesis"
  | "complete"
  | "failed";

export interface AnalysisJobStatus {
  job_id: string;
  stage: AnalysisStage;
  progress_pct: number;
  error: string | null;
  created_at: string;
  updated_at: string;
}

export interface AnalysisStartResponse {
  job_id: string;
  status: AnalysisStage;
}

export interface DocumentInfo {
  document_name: string;
  chunks: number;
  pages: number;
  is_demo_data: boolean;
  category: DocumentCategory;
  status: string;
}

export interface DocumentListResponse {
  documents: DocumentInfo[];
  total_chunks: number;
  last_indexed_at: string | null;
}
