export type TruthGuardStatus = "VERIFIED" | "PARTIALLY_SUPPORTED" | "UNSUPPORTED" | "REQUIRES_REVIEW";

export type SuggestionType = "EMPHASIZE" | "REPHRASE" | "REORDER" | "REMOVE" | "ADD_FROM_PROFILE";

export type SuggestionStatus = "PENDING" | "ACCEPTED" | "REJECTED" | "MODIFIED";

export interface SuggestionEvidence {
  id: string;
  suggestion_id: string;
  evidence_type: "SKILL" | "EXPERIENCE" | "PROJECT" | "EDUCATION" | "CERTIFICATION";
  evidence_id?: string | null;
  source: string;
  supporting_text?: string | null;
  confidence: number;
  created_at: string;
}

export interface ClaimBreakdownItem {
  claim_text: string;
  status: TruthGuardStatus;
  reasons: string[];
  detected_metrics: string[];
  unsupported_metrics: string[];
  detected_skills: string[];
  unsupported_skills: string[];
}

export interface ResumeSuggestion {
  id: string;
  tailoring_job_id: string;
  resume_version_id: string;
  section: "SUMMARY" | "SKILLS" | "EXPERIENCE" | "PROJECTS" | "EDUCATION" | "CERTIFICATIONS" | string;
  suggestion_type: SuggestionType;
  original_content?: string | null;
  proposed_content: string;
  reason: string;
  confidence: number;
  status: SuggestionStatus;
  truth_guard_status: TruthGuardStatus;
  truth_guard_reason?: string | null;
  claim_breakdown_json?: ClaimBreakdownItem[] | null;
  user_notes?: string | null;
  created_at: string;
  updated_at: string;
  evidence_items?: SuggestionEvidence[];
}

export interface ResumeTailoringJob {
  id: string;
  user_id: string;
  resume_version_id: string;
  job_description_id: string;
  status: "PENDING" | "PROCESSING" | "COMPLETED" | "FAILED";
  prompt_version: string;
  model_metadata?: Record<string, any> | null;
  error_detail?: string | null;
  created_at: string;
  updated_at: string;
  suggestions: ResumeSuggestion[];
}

export interface TailorTriggerRequest {
  job_description_id: string;
  prompt_override?: string;
}

export interface SuggestionUpdateRequest {
  status: SuggestionStatus;
  proposed_content?: string;
  user_notes?: string;
}

export interface ApplySuggestionsRequest {
  suggestion_ids: string[];
  change_summary?: string;
  trigger_match?: boolean;
}

export interface LineDiffItem {
  type: "ADD" | "REMOVE" | "UNCHANGED";
  content: string;
}

export interface SectionDiffItem {
  has_changes: boolean;
  similarity_ratio: number;
  added_lines: number;
  removed_lines: number;
  diff: LineDiffItem[];
}

export interface VersionDiffResponse {
  original_version_id: string;
  compared_version_id: string;
  similarity_ratio: number;
  added_lines: number;
  removed_lines: number;
  unified_diff: string;
  line_diffs: LineDiffItem[];
  section_diffs?: Record<string, SectionDiffItem> | null;
}

export interface MatchScoreSnapshot {
  overall_score: number;
  required_skills_score: number;
  preferred_skills_score: number;
  experience_score: number;
  project_score: number;
  semantic_score: number;
  matched_count: number;
  missing_count: number;
}

export interface TailoringApplyResponse {
  new_version_id: string;
  version_number: string;
  parent_version_id: string;
  accepted_count: number;
  diff: VersionDiffResponse;
  before_match?: MatchScoreSnapshot | null;
  after_match?: MatchScoreSnapshot | null;
  score_delta?: number | null;
  score_improved: boolean;
}
