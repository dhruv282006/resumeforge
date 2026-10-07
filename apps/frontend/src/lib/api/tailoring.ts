import { apiClient } from "./client";
import type {
  ApplySuggestionsRequest,
  ResumeSuggestion,
  ResumeTailoringJob,
  SuggestionUpdateRequest,
  TailorTriggerRequest,
  TailoringApplyResponse,
  VersionDiffResponse,
} from "@/types/tailoring";

export const tailoringApi = {
  // Trigger AI tailoring for a specific resume version and target job description
  async triggerTailoring(
    versionId: string,
    payload: TailorTriggerRequest
  ): Promise<ResumeTailoringJob> {
    return apiClient.post<ResumeTailoringJob>(
      `/api/v1/resumes/${versionId}/tailor`,
      payload
    );
  },

  // Get details of a tailoring job
  async getTailoringJob(
    jobId: string,
    versionId?: string
  ): Promise<ResumeTailoringJob> {
    const url = versionId
      ? `/api/v1/resumes/${versionId}/tailoring-jobs/${jobId}`
      : `/api/v1/resumes/tailoring-jobs/${jobId}`;
    return apiClient.get<ResumeTailoringJob>(url);
  },

  // List all tailoring jobs for a resume version
  async listVersionTailoringJobs(versionId: string): Promise<ResumeTailoringJob[]> {
    return apiClient.get<ResumeTailoringJob[]>(
      `/api/v1/resumes/${versionId}/tailoring-jobs`
    );
  },

  // Update/review an individual suggestion (accept, reject, edit)
  async updateSuggestion(
    suggestionId: string,
    payload: SuggestionUpdateRequest
  ): Promise<ResumeSuggestion> {
    return apiClient.patch<ResumeSuggestion>(
      `/api/v1/resumes/suggestions/${suggestionId}`,
      payload
    );
  },

  // Apply accepted suggestions, clone a new immutable version, compute diff and re-score
  async applySuggestions(
    versionId: string,
    payload: ApplySuggestionsRequest
  ): Promise<TailoringApplyResponse> {
    return apiClient.post<TailoringApplyResponse>(
      `/api/v1/resumes/${versionId}/apply-suggestions`,
      payload
    );
  },

  // Get transparent text and section diff between two versions
  async getVersionDiff(
    versionId: string,
    compareVersionId: string
  ): Promise<VersionDiffResponse> {
    return apiClient.get<VersionDiffResponse>(
      `/api/v1/resumes/${versionId}/diff/${compareVersionId}`
    );
  },
};
