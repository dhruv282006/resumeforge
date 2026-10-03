export interface EducationItem {
  id: string;
  profile_id?: string;
  institution: string;
  degree?: string | null;
  field_of_study?: string | null;
  location?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  is_current?: boolean;
  gpa?: number | null;
  percentage?: number | null;
  description?: string | null;
  created_at?: string;
  updated_at?: string;
}

export type SkillSource = "USER_PROVIDED" | "RESUME_PARSED" | "AI_INFERRED" | "IMPORTED";

export interface SkillItem {
  id: string;
  profile_id?: string;
  name: string;
  normalized_name?: string | null;
  category?: string | null;
  proficiency?: string | null;
  years_of_experience?: number | null;
  source: SkillSource | string;
  confidence?: number;
  created_at?: string;
  updated_at?: string;
}

export interface ExperienceItem {
  id: string;
  profile_id?: string;
  company: string;
  title: string;
  employment_type?: string | null;
  location?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  is_current: boolean;
  description?: string | null;
  achievements: string[];
  source?: string;
  confidence?: number;
  created_at?: string;
  updated_at?: string;
}

export interface ProjectItem {
  id: string;
  profile_id?: string;
  name: string;
  description?: string | null;
  technologies: string[];
  role?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  project_url?: string | null;
  github_url?: string | null;
  achievements?: string[];
  metrics?: string[];
  created_at?: string;
  updated_at?: string;
}

export interface CertificationItem {
  id: string;
  profile_id?: string;
  name: string;
  issuing_organization?: string | null;
  issue_date?: string | null;
  expiry_date?: string | null;
  credential_id?: string | null;
  credential_url?: string | null;
  created_at?: string;
  updated_at?: string;
}

export interface MasterProfile {
  id: string;
  user_id: string;
  full_name: string;
  headline?: string | null;
  summary?: string | null;
  email?: string | null;
  phone?: string | null;
  location?: string | null;
  linkedin_url?: string | null;
  github_url?: string | null;
  portfolio_url?: string | null;
  preferred_roles: string[];
  preferred_industries: string[];
  preferred_locations: string[];
  years_of_experience?: number | null;
  current_status?: string | null;
  educations: EducationItem[];
  experiences: ExperienceItem[];
  skills: SkillItem[];
  projects: ProjectItem[];
  certifications: CertificationItem[];
  created_at: string;
  updated_at: string;
}

export interface ProfileCompleteness {
  overall: number;
  sections: {
    personal: number;
    education: number;
    experience: number;
    skills: number;
    projects: number;
    certifications: number;
    links: number;
    [key: string]: number;
  };
}

export interface UpdateProfilePayload {
  full_name?: string;
  headline?: string;
  summary?: string;
  email?: string;
  phone?: string;
  location?: string;
  linkedin_url?: string;
  github_url?: string;
  portfolio_url?: string;
  preferred_roles?: string[];
  preferred_industries?: string[];
  preferred_locations?: string[];
  years_of_experience?: number;
  current_status?: string;
}
