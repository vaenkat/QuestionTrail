/**
 * TypeScript data models mirroring QuestionTrail domain contracts.
 */

export type SourceType = 'webpage' | 'document' | 'pdf' | 'api' | 'manual';
export type SourceAuthority = 'primary_official' | 'secondary_authoritative' | 'third_party' | 'unknown';
export type AssessmentStatus = 'supported' | 'partially_covered' | 'conflicting' | 'unsupported' | 'requires_verification';
export type FindingType = 'potential_conflict' | 'dated_information' | 'information_gap' | 'unsupported_assertion' | 'consistency_signal';
export type FindingLabel = 'potential' | 'confirmed';
export type FindingSeverity = 'low' | 'medium' | 'high' | 'critical';

export interface EvidenceRef {
  source_id: string;
  exact_snippet: string;
  location_type: string;
  location_value: string;
  page_number?: number | null;
  metadata?: Record<string, unknown>;
}

export interface Source {
  id: string;
  title: string;
  url?: string | null;
  type: SourceType;
  authority: SourceAuthority;
  publication_date?: string | null;
  cycle_or_version?: string | null;
  retrieved_at: string;
  extraction_status: string;
  content_hash?: string | null;
  raw_content?: string | null;
  metadata?: Record<string, unknown>;
}

export interface Claim {
  id: string;
  normalized_statement: string;
  entities: string[];
  dates: string[];
  evidence_refs: EvidenceRef[];
  extraction_status: string;
  is_verified: boolean;
}

export interface AssessmentCategory {
  id: string;
  name: string;
  description: string;
  evaluation_question: string;
  enabled: boolean;
  is_ai_suggested?: boolean;
}

export interface CategoryAssessment {
  category_id: string;
  status: AssessmentStatus;
  supporting_claim_ids: string[];
  contrary_claim_ids: string[];
  unanswered_questions: string[];
  rationale?: string | null;
}

export interface Finding {
  id: string;
  type: FindingType;
  label: FindingLabel;
  severity: FindingSeverity;
  rationale: string;
  evidence_refs: EvidenceRef[];
  sources_examined?: string[];
  scope_examined?: string | null;
  contrasting_claim_ids?: string[];
}

export interface VerificationAction {
  id: string;
  priority_score: number;
  action: string;
  rationale: string;
  recommended_source?: string | null;
  linked_claim_ids?: string[];
  linked_finding_ids?: string[];
  completed?: boolean;
}

export interface AnalysisResult {
  project_id: string;
  dataset_hash: string;
  analysis_schema_version: string;
  sources: Source[];
  claims: Claim[];
  assessments: CategoryAssessment[];
  findings: Finding[];
  actions: VerificationAction[];
  summary?: string | null;
  created_at: string;
}

export interface ResearchProject {
  id: string;
  objective: string;
  categories: AssessmentCategory[];
  source_ids: string[];
  dataset_hash?: string | null;
  analysis_schema_version: string;
  created_at: string;
  updated_at: string;
}

export interface ProjectDetailResponse {
  project: ResearchProject;
  sources: Source[];
  has_analysis: boolean;
}

export interface AnalyzeProjectResponse {
  result: AnalysisResult;
  mode: 'precomputed' | 'mock' | 'live';
}

export interface ReportResponse {
  project_id: string;
  objective: string;
  summary: string;
  markdown_report: string;
  total_claims: number;
  total_findings: number;
  total_actions: number;
}
