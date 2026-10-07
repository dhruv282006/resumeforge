import { apiClient } from "./client";
import type {
  ResumeItem,
  ResumeVersion,
  CreateResumePayload,
  UpdateResumePayload,
  CreateVersionPayload,
  CloneVersionPayload,
} from "@/types/resume";

export const resumesApi = {
  // GET List of Resumes
  async getResumes(): Promise<ResumeItem[]> {
    return apiClient.get<ResumeItem[]>("/api/v1/resumes");
  },

  // POST Create Resume
  async createResume(payload: CreateResumePayload): Promise<ResumeItem> {
    return apiClient.post<ResumeItem>("/api/v1/resumes", payload);
  },

  // GET Single Resume
  async getResume(id: string): Promise<ResumeItem> {
    return apiClient.get<ResumeItem>(`/api/v1/resumes/${id}`);
  },

  // PUT Update Resume
  async updateResume(id: string, payload: UpdateResumePayload): Promise<ResumeItem> {
    return apiClient.put<ResumeItem>(`/api/v1/resumes/${id}`, payload);
  },

  // DELETE Resume
  async deleteResume(id: string): Promise<{ success: boolean }> {
    return apiClient.delete<{ success: boolean }>(`/api/v1/resumes/${id}`);
  },

  // --- Resume Versions ---

  // GET Versions list for a Resume
  async getResumeVersions(resumeId: string): Promise<ResumeVersion[]> {
    return apiClient.get<ResumeVersion[]>(`/api/v1/resumes/${resumeId}/versions`);
  },

  // GET Single Resume Version
  async getResumeVersion(resumeId: string, versionId: string): Promise<ResumeVersion> {
    return apiClient.get<ResumeVersion>(`/api/v1/resumes/${resumeId}/versions/${versionId}`);
  },

  // POST Create Version (Text based or manually cloned)
  async createResumeVersion(resumeId: string, payload: CreateVersionPayload): Promise<ResumeVersion> {
    return apiClient.post<ResumeVersion>(`/api/v1/resumes/${resumeId}/versions`, payload);
  },

  // POST Upload Resume Version file (.pdf or .docx)
  async uploadResumeVersion(
    resumeId: string,
    file: File,
    versionNumber?: string,
    changeSummary?: string
  ): Promise<ResumeVersion> {
    const formData = new FormData();
    formData.append("file", file);
    if (versionNumber) {
      formData.append("version_number", versionNumber);
    }
    if (changeSummary) {
      formData.append("change_summary", changeSummary);
    }

    const baseUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
    const response = await fetch(`${baseUrl.replace(/\/$/, "")}/api/v1/resumes/${resumeId}/versions/upload`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      let errorMsg = `Upload failed with status ${response.status}`;
      try {
        const parsed = await response.json();
        if (parsed.detail) errorMsg = typeof parsed.detail === "string" ? parsed.detail : JSON.stringify(parsed.detail);
        else if (parsed.message) errorMsg = parsed.message;
      } catch {
        // ignore
      }
      throw new Error(errorMsg);
    }

    return response.json();
  },

  // POST Clone Resume Version
  async cloneResumeVersion(
    resumeId: string,
    versionId: string,
    payload: CloneVersionPayload
  ): Promise<ResumeVersion> {
    return apiClient.post<ResumeVersion>(
      `/api/v1/resumes/${resumeId}/versions/${versionId}/clone`,
      payload
    );
  },

  // POST Activate Resume Version
  async activateResumeVersion(resumeId: string, versionId: string): Promise<ResumeItem> {
    return apiClient.post<ResumeItem>(`/api/v1/resumes/${resumeId}/versions/${versionId}/activate`, {});
  },
};
