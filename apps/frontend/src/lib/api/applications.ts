import { apiClient } from "./client";
import type {
  ApplicationItem,
  ApplicationStats,
  CreateApplicationPayload,
  UpdateApplicationPayload,
} from "@/types/application";

export const applicationsApi = {
  // GET all applications
  async getApplications(status?: string): Promise<ApplicationItem[]> {
    const qs = status ? `?status=${encodeURIComponent(status)}` : "";
    return apiClient.get<ApplicationItem[]>(`/api/v1/applications${qs}`);
  },

  // GET stats
  async getStats(): Promise<ApplicationStats> {
    return apiClient.get<ApplicationStats>("/api/v1/applications/stats");
  },

  // GET single application
  async getApplication(id: string): Promise<ApplicationItem> {
    return apiClient.get<ApplicationItem>(`/api/v1/applications/${id}`);
  },

  // POST create application
  async createApplication(payload: CreateApplicationPayload): Promise<ApplicationItem> {
    return apiClient.post<ApplicationItem>("/api/v1/applications", payload);
  },

  // PUT update application
  async updateApplication(
    id: string,
    payload: UpdateApplicationPayload
  ): Promise<ApplicationItem> {
    return apiClient.put<ApplicationItem>(`/api/v1/applications/${id}`, payload);
  },

  // DELETE application
  async deleteApplication(id: string): Promise<void> {
    return apiClient.delete<void>(`/api/v1/applications/${id}`);
  },
};
