import { apiClient } from "./client";
import type {
  MasterProfile,
  ProfileCompleteness,
  EducationItem,
  ExperienceItem,
  SkillItem,
  ProjectItem,
  CertificationItem,
  UpdateProfilePayload,
} from "@/types/profile";

export const profileApi = {
  // GET Profile
  async getProfile(): Promise<MasterProfile> {
    return apiClient.get<MasterProfile>("/api/v1/profile");
  },

  // PUT Profile main info & preferences
  async updateProfile(payload: UpdateProfilePayload): Promise<MasterProfile> {
    return apiClient.put<MasterProfile>("/api/v1/profile", payload);
  },

  // GET Completeness
  async getProfileCompleteness(): Promise<ProfileCompleteness> {
    return apiClient.get<ProfileCompleteness>("/api/v1/profile/completeness");
  },

  // --- Education CRUD ---
  async addEducation(item: Omit<EducationItem, "id" | "created_at" | "updated_at">): Promise<EducationItem> {
    return apiClient.post<EducationItem>("/api/v1/profile/education", item);
  },

  async updateEducation(id: string, item: Partial<EducationItem>): Promise<EducationItem> {
    return apiClient.put<EducationItem>(`/api/v1/profile/education/${id}`, item);
  },

  async deleteEducation(id: string): Promise<void> {
    return apiClient.delete<void>(`/api/v1/profile/education/${id}`);
  },

  // --- Experience CRUD ---
  async addExperience(item: Omit<ExperienceItem, "id" | "created_at" | "updated_at">): Promise<ExperienceItem> {
    return apiClient.post<ExperienceItem>("/api/v1/profile/experience", item);
  },

  async updateExperience(id: string, item: Partial<ExperienceItem>): Promise<ExperienceItem> {
    return apiClient.put<ExperienceItem>(`/api/v1/profile/experience/${id}`, item);
  },

  async deleteExperience(id: string): Promise<void> {
    return apiClient.delete<void>(`/api/v1/profile/experience/${id}`);
  },

  // --- Skills CRUD ---
  async addSkill(item: Omit<SkillItem, "id" | "created_at" | "updated_at">): Promise<SkillItem> {
    return apiClient.post<SkillItem>("/api/v1/profile/skills", item);
  },

  async updateSkill(id: string, item: Partial<SkillItem>): Promise<SkillItem> {
    return apiClient.put<SkillItem>(`/api/v1/profile/skills/${id}`, item);
  },

  async deleteSkill(id: string): Promise<void> {
    return apiClient.delete<void>(`/api/v1/profile/skills/${id}`);
  },

  // --- Projects CRUD ---
  async addProject(item: Omit<ProjectItem, "id" | "created_at" | "updated_at">): Promise<ProjectItem> {
    return apiClient.post<ProjectItem>("/api/v1/profile/projects", item);
  },

  async updateProject(id: string, item: Partial<ProjectItem>): Promise<ProjectItem> {
    return apiClient.put<ProjectItem>(`/api/v1/profile/projects/${id}`, item);
  },

  async deleteProject(id: string): Promise<void> {
    return apiClient.delete<void>(`/api/v1/profile/projects/${id}`);
  },

  // --- Certifications CRUD ---
  async addCertification(item: Omit<CertificationItem, "id" | "created_at" | "updated_at">): Promise<CertificationItem> {
    return apiClient.post<CertificationItem>("/api/v1/profile/certifications", item);
  },

  async updateCertification(id: string, item: Partial<CertificationItem>): Promise<CertificationItem> {
    return apiClient.put<CertificationItem>(`/api/v1/profile/certifications/${id}`, item);
  },

  async deleteCertification(id: string): Promise<void> {
    return apiClient.delete<void>(`/api/v1/profile/certifications/${id}`);
  },
};
