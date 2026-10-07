import { apiClient } from "./client";
import type {
  JobDescription,
  JobCreate,
  JobUpdate,
  JobAnalysis,
  JobRequirement,
  JobMatch,
  JobMatchRequest,
} from "@/types/job";

export const jobsApi = {
  // List all jobs
  async getJobs(): Promise<JobDescription[]> {
    return apiClient.get<JobDescription[]>("/api/v1/jobs");
  },

  // Create a new job description
  async createJob(payload: JobCreate): Promise<JobDescription> {
    return apiClient.post<JobDescription>("/api/v1/jobs", payload);
  },

  // Get job details by ID
  async getJob(id: string): Promise<JobDescription> {
    return apiClient.get<JobDescription>(`/api/v1/jobs/${id}`);
  },

  // Update job
  async updateJob(id: string, payload: JobUpdate): Promise<JobDescription> {
    return apiClient.put<JobDescription>(`/api/v1/jobs/${id}`, payload);
  },

  // Delete job
  async deleteJob(id: string): Promise<void> {
    return apiClient.delete<void>(`/api/v1/jobs/${id}`);
  },

  // Trigger analysis pipeline
  async analyzeJob(id: string): Promise<JobAnalysis> {
    return apiClient.post<JobAnalysis>(`/api/v1/jobs/${id}/analyze`);
  },

  // Get analysis results
  async getJobAnalysis(id: string): Promise<JobAnalysis> {
    return apiClient.get<JobAnalysis>(`/api/v1/jobs/${id}/analysis`);
  },

  // List requirements with optional category/importance filters
  async getJobRequirements(
    id: string,
    params?: { category?: string; importance?: string }
  ): Promise<JobRequirement[]> {
    const query = new URLSearchParams();
    if (params?.category) query.set("category", params.category);
    if (params?.importance) query.set("importance", params.importance);
    const qs = query.toString() ? `?${query.toString()}` : "";
    return apiClient.get<JobRequirement[]>(`/api/v1/jobs/${id}/requirements${qs}`);
  },

  // Trigger hybrid semantic matching
  async matchJob(id: string, payload: JobMatchRequest): Promise<JobMatch> {
    return apiClient.post<JobMatch>(`/api/v1/jobs/${id}/match`, payload);
  },

  // List all matches for a job
  async getJobMatches(id: string): Promise<JobMatch[]> {
    return apiClient.get<JobMatch[]>(`/api/v1/jobs/${id}/matches`);
  },

  // Get a specific match report
  async getJobMatch(id: string, matchId: string): Promise<JobMatch> {
    return apiClient.get<JobMatch>(`/api/v1/jobs/${id}/matches/${matchId}`);
  },
};
