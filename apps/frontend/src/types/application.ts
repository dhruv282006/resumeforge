export type ApplicationStatus =
  | "APPLIED"
  | "SCREENING"
  | "INTERVIEWING"
  | "OFFERED"
  | "REJECTED"
  | "WITHDRAWN";

export interface ApplicationItem {
  id: string;
  user_id: string;
  company: string;
  position: string;
  status: ApplicationStatus | string;
  location?: string | null;
  salary_range?: string | null;
  job_url?: string | null;
  applied_date?: string | null;
  notes?: string | null;
  job_id?: string | null;
  resume_id?: string | null;
  resume_version_id?: string | null;
  created_at: string;
  updated_at: string;
}

export interface CreateApplicationPayload {
  company: string;
  position: string;
  status?: string;
  location?: string;
  salary_range?: string;
  job_url?: string;
  applied_date?: string;
  notes?: string;
  job_id?: string;
  resume_id?: string;
  resume_version_id?: string;
}

export interface UpdateApplicationPayload {
  company?: string;
  position?: string;
  status?: string;
  location?: string;
  salary_range?: string;
  job_url?: string;
  applied_date?: string;
  notes?: string;
  job_id?: string;
  resume_id?: string;
  resume_version_id?: string;
}

export interface ApplicationStats {
  total: number;
  applied: number;
  screening: number;
  interviewing: number;
  offered: number;
  rejected: number;
  withdrawn: number;
}
