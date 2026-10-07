"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { profileApi } from "@/lib/api/profile";
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

export function useProfile() {
  const queryClient = useQueryClient();

  const profileQuery = useQuery<MasterProfile>({
    queryKey: ["profile"],
    queryFn: () => profileApi.getProfile(),
  });

  const completenessQuery = useQuery<ProfileCompleteness>({
    queryKey: ["profile", "completeness"],
    queryFn: () => profileApi.getProfileCompleteness(),
  });

  const updateProfileMutation = useMutation({
    mutationFn: (payload: UpdateProfilePayload) => profileApi.updateProfile(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["profile"] });
      queryClient.invalidateQueries({ queryKey: ["profile", "completeness"] });
    },
  });

  // --- Education Mutations ---
  const addEducationMutation = useMutation({
    mutationFn: (item: Omit<EducationItem, "id" | "created_at" | "updated_at">) =>
      profileApi.addEducation(item),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["profile"] });
      queryClient.invalidateQueries({ queryKey: ["profile", "completeness"] });
    },
  });

  const updateEducationMutation = useMutation({
    mutationFn: ({ id, item }: { id: string; item: Partial<EducationItem> }) =>
      profileApi.updateEducation(id, item),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["profile"] });
      queryClient.invalidateQueries({ queryKey: ["profile", "completeness"] });
    },
  });

  const deleteEducationMutation = useMutation({
    mutationFn: (id: string) => profileApi.deleteEducation(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["profile"] });
      queryClient.invalidateQueries({ queryKey: ["profile", "completeness"] });
    },
  });

  // --- Experience Mutations ---
  const addExperienceMutation = useMutation({
    mutationFn: (item: Omit<ExperienceItem, "id" | "created_at" | "updated_at">) =>
      profileApi.addExperience(item),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["profile"] });
      queryClient.invalidateQueries({ queryKey: ["profile", "completeness"] });
    },
  });

  const updateExperienceMutation = useMutation({
    mutationFn: ({ id, item }: { id: string; item: Partial<ExperienceItem> }) =>
      profileApi.updateExperience(id, item),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["profile"] });
      queryClient.invalidateQueries({ queryKey: ["profile", "completeness"] });
    },
  });

  const deleteExperienceMutation = useMutation({
    mutationFn: (id: string) => profileApi.deleteExperience(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["profile"] });
      queryClient.invalidateQueries({ queryKey: ["profile", "completeness"] });
    },
  });

  // --- Skills Mutations ---
  const addSkillMutation = useMutation({
    mutationFn: (item: Omit<SkillItem, "id" | "created_at" | "updated_at">) =>
      profileApi.addSkill(item),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["profile"] });
      queryClient.invalidateQueries({ queryKey: ["profile", "completeness"] });
    },
  });

  const updateSkillMutation = useMutation({
    mutationFn: ({ id, item }: { id: string; item: Partial<SkillItem> }) =>
      profileApi.updateSkill(id, item),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["profile"] });
      queryClient.invalidateQueries({ queryKey: ["profile", "completeness"] });
    },
  });

  const deleteSkillMutation = useMutation({
    mutationFn: (id: string) => profileApi.deleteSkill(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["profile"] });
      queryClient.invalidateQueries({ queryKey: ["profile", "completeness"] });
    },
  });

  // --- Projects Mutations ---
  const addProjectMutation = useMutation({
    mutationFn: (item: Omit<ProjectItem, "id" | "created_at" | "updated_at">) =>
      profileApi.addProject(item),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["profile"] });
      queryClient.invalidateQueries({ queryKey: ["profile", "completeness"] });
    },
  });

  const updateProjectMutation = useMutation({
    mutationFn: ({ id, item }: { id: string; item: Partial<ProjectItem> }) =>
      profileApi.updateProject(id, item),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["profile"] });
      queryClient.invalidateQueries({ queryKey: ["profile", "completeness"] });
    },
  });

  const deleteProjectMutation = useMutation({
    mutationFn: (id: string) => profileApi.deleteProject(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["profile"] });
      queryClient.invalidateQueries({ queryKey: ["profile", "completeness"] });
    },
  });

  // --- Certifications Mutations ---
  const addCertificationMutation = useMutation({
    mutationFn: (item: Omit<CertificationItem, "id" | "created_at" | "updated_at">) =>
      profileApi.addCertification(item),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["profile"] });
      queryClient.invalidateQueries({ queryKey: ["profile", "completeness"] });
    },
  });

  const updateCertificationMutation = useMutation({
    mutationFn: ({ id, item }: { id: string; item: Partial<CertificationItem> }) =>
      profileApi.updateCertification(id, item),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["profile"] });
      queryClient.invalidateQueries({ queryKey: ["profile", "completeness"] });
    },
  });

  const deleteCertificationMutation = useMutation({
    mutationFn: (id: string) => profileApi.deleteCertification(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["profile"] });
      queryClient.invalidateQueries({ queryKey: ["profile", "completeness"] });
    },
  });

  return {
    profile: profileQuery.data,
    completeness: completenessQuery.data,
    isLoading: profileQuery.isLoading || completenessQuery.isLoading,
    isError: profileQuery.isError,
    refetch: () => {
      profileQuery.refetch();
      completenessQuery.refetch();
    },

    // Mutations
    updateProfile: updateProfileMutation.mutateAsync,
    isUpdatingProfile: updateProfileMutation.isPending,

    addEducation: addEducationMutation.mutateAsync,
    updateEducation: updateEducationMutation.mutateAsync,
    deleteEducation: deleteEducationMutation.mutateAsync,

    addExperience: addExperienceMutation.mutateAsync,
    updateExperience: updateExperienceMutation.mutateAsync,
    deleteExperience: deleteExperienceMutation.mutateAsync,

    addSkill: addSkillMutation.mutateAsync,
    updateSkill: updateSkillMutation.mutateAsync,
    deleteSkill: deleteSkillMutation.mutateAsync,

    addProject: addProjectMutation.mutateAsync,
    updateProject: updateProjectMutation.mutateAsync,
    deleteProject: deleteProjectMutation.mutateAsync,

    addCertification: addCertificationMutation.mutateAsync,
    updateCertification: updateCertificationMutation.mutateAsync,
    deleteCertification: deleteCertificationMutation.mutateAsync,
  };
}
