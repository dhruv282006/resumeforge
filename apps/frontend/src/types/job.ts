export type RequirementCategory =
  | 'SKILL'
  | 'EXPERIENCE'
  | 'EDUCATION'
  | 'RESPONSIBILITY'
  | 'CERTIFICATION'
  | 'DOMAIN_KNOWLEDGE'
  | 'OTHER';

export type RequirementImportance = 'REQUIRED' | 'PREFERRED' | 'OPTIONAL' | 'UNKNOWN';

export type MatchStatus = 'MATCHED' | 'PARTIAL' | 'MISSING' | 'UNKNOWN';

export interface MatchingWeights {
  required_skills: number;
  preferred_skills: number;
  experience_relevance: number;
  project_relevance: number;
  semantic_alignment: number;
}

export interface JobRequirement {
  id: string;
  job_id: string;
  text: string;
  category: RequirementCategory;
  importance: RequirementImportance;
  extracted_skill?: string | null;
  min_experience_years?: number | null;
  confidence: number;
  source_section: string;
  created_at: string;
}

export interface JobSkillRequirement {
  id: string;
  job_id: string;
  requirement_id?: string | null;
  skill_name: string;
  normalized_skill: string;
  category: string;
  importance: string;
  min_years?: number | null;
  confidence: number;
  created_at: string;
}

export interface JobAnalysis {
  id: string;
  job_id: string;
  status: string;
  summary?: string | null;
  total_requirements: number;
  total_skills: number;
  raw_analysis_json?: Record<string, unknown> | null;
  created_at: string;
}

export interface JobDescription {
  id: string;
  user_id: string;
  title?: string | null;
  company?: string | null;
  location?: string | null;
  employment_type?: string | null;
  source_url?: string | null;
  raw_text: string;
  normalized_text?: string | null;
  status: string;
  created_at: string;
  updated_at: string;
  analysis?: JobAnalysis | null;
  requirements?: JobRequirement[];
  skills?: JobSkillRequirement[];
}

export interface JobCreate {
  title?: string;
  company?: string;
  location?: string;
  employment_type?: string;
  source_url?: string;
  raw_text: string;
}

export interface JobUpdate {
  title?: string;
  company?: string;
  location?: string;
  employment_type?: string;
  source_url?: string;
  raw_text?: string;
  status?: string;
}

export interface JobMatchItem {
  id: string;
  match_id: string;
  requirement_id: string;
  status: MatchStatus;
  score: number;
  matched_entity_type?: string | null;
  matched_entity_id?: string | null;
  matched_entity_name?: string | null;
  evidence_summary?: string | null;
  evidence_source: string;
  explanation?: string | null;
  created_at: string;
}

export interface JobMatchBreakdown {
  required_skills: number;
  preferred_skills: number;
  experience_relevance: number;
  project_relevance: number;
  semantic_alignment: number;
}

export interface JobMatch {
  id: string;
  job_id: string;
  user_id: string;
  profile_id?: string | null;
  resume_version_id?: string | null;
  target_type: 'PROFILE' | 'RESUME_VERSION';
  overall_score: number;
  breakdown_scores: JobMatchBreakdown;
  status: string;
  error_message?: string | null;
  config_json?: Record<string, unknown> | null;
  created_at: string;
  items: JobMatchItem[];
}

export interface JobMatchRequest {
  target_type?: 'PROFILE' | 'RESUME_VERSION';
  resume_version_id?: string | null;
  weights?: MatchingWeights | null;
}
