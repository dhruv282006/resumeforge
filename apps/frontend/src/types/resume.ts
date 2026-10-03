export type VersionStatus = "UPLOADED" | "PROCESSING" | "READY" | "FAILED";

export interface ResumeVersion {
  id: string;
  resume_id: string;
  version_number: string;
  parent_version_id?: string | null;
  target_job_id?: string | null;
  file_path?: string | null;
  extracted_text?: string | null;
  structured_snapshot?: unknown;
  change_summary?: string | null;
  status: VersionStatus | string;
  error_detail?: string | null;
  created_at: string;
  created_by?: string | null;
}

export interface ResumeItem {
  id: string;
  user_id: string;
  title: string;
  description?: string | null;
  target_role?: string | null;
  target_company?: string | null;
  active_version_id?: string | null;
  status: string;
  created_at: string;
  updated_at: string;
  versions: ResumeVersion[];
}

export interface CreateResumePayload {
  title: string;
  target_role?: string;
  target_company?: string;
  description?: string;
  initial_version_number?: string;
}

export interface UpdateResumePayload {
  title?: string;
  target_role?: string;
  target_company?: string;
  description?: string;
  active_version_id?: string;
  status?: string;
}

export interface CreateVersionPayload {
  version_number: string;
  change_summary?: string;
  parent_version_id?: string;
  extracted_text?: string;
  structured_snapshot?: unknown;
}

export interface CloneVersionPayload {
  version_number: string;
  change_summary?: string;
}

export interface UploadVersionPayload {
  file: File;
  version_number?: string;
  change_summary?: string;
}
