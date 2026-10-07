"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { resumesApi } from "@/lib/api/resumes";
import type {
  ResumeItem,
  ResumeVersion,
  CreateResumePayload,
  UpdateResumePayload,
  CreateVersionPayload,
  CloneVersionPayload,
} from "@/types/resume";

export function useResumes() {
  const queryClient = useQueryClient();

  const query = useQuery<ResumeItem[]>({
    queryKey: ["resumes"],
    queryFn: () => resumesApi.getResumes(),
  });

  const createResumeMutation = useMutation({
    mutationFn: (payload: CreateResumePayload) => resumesApi.createResume(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["resumes"] });
    },
  });

  const deleteResumeMutation = useMutation({
    mutationFn: (id: string) => resumesApi.deleteResume(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["resumes"] });
    },
  });

  return {
    resumes: query.data ?? [],
    isLoading: query.isLoading,
    isError: query.isError,
    refetch: query.refetch,
    createResume: createResumeMutation.mutateAsync,
    isCreating: createResumeMutation.isPending,
    deleteResume: deleteResumeMutation.mutateAsync,
    isDeleting: deleteResumeMutation.isPending,
  };
}

export function useResumeDetail(resumeId: string) {
  const queryClient = useQueryClient();

  const resumeQuery = useQuery<ResumeItem>({
    queryKey: ["resume", resumeId],
    queryFn: () => resumesApi.getResume(resumeId),
    enabled: !!resumeId,
  });

  const versionsQuery = useQuery<ResumeVersion[]>({
    queryKey: ["resume-versions", resumeId],
    queryFn: () => resumesApi.getResumeVersions(resumeId),
    enabled: !!resumeId,
  });

  const updateResumeMutation = useMutation({
    mutationFn: (payload: UpdateResumePayload) => resumesApi.updateResume(resumeId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["resume", resumeId] });
      queryClient.invalidateQueries({ queryKey: ["resumes"] });
    },
  });

  const createVersionMutation = useMutation({
    mutationFn: (payload: CreateVersionPayload) => resumesApi.createResumeVersion(resumeId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["resume-versions", resumeId] });
      queryClient.invalidateQueries({ queryKey: ["resume", resumeId] });
    },
  });

  const uploadVersionMutation = useMutation({
    mutationFn: ({
      file,
      versionNumber,
      changeSummary,
    }: {
      file: File;
      versionNumber?: string;
      changeSummary?: string;
    }) => resumesApi.uploadResumeVersion(resumeId, file, versionNumber, changeSummary),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["resume-versions", resumeId] });
      queryClient.invalidateQueries({ queryKey: ["resume", resumeId] });
    },
  });

  const cloneVersionMutation = useMutation({
    mutationFn: ({
      versionId,
      payload,
    }: {
      versionId: string;
      payload: CloneVersionPayload;
    }) => resumesApi.cloneResumeVersion(resumeId, versionId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["resume-versions", resumeId] });
      queryClient.invalidateQueries({ queryKey: ["resume", resumeId] });
    },
  });

  const activateVersionMutation = useMutation({
    mutationFn: (versionId: string) => resumesApi.activateResumeVersion(resumeId, versionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["resume-versions", resumeId] });
      queryClient.invalidateQueries({ queryKey: ["resume", resumeId] });
      queryClient.invalidateQueries({ queryKey: ["resumes"] });
    },
  });

  return {
    resume: resumeQuery.data,
    versions: versionsQuery.data ?? resumeQuery.data?.versions ?? [],
    isLoading: resumeQuery.isLoading || versionsQuery.isLoading,
    isVersionsLoading: versionsQuery.isLoading,
    isError: resumeQuery.isError,

    updateResume: updateResumeMutation.mutateAsync,
    createVersion: createVersionMutation.mutateAsync,
    uploadVersion: uploadVersionMutation.mutateAsync,
    cloneVersion: cloneVersionMutation.mutateAsync,
    activateVersion: activateVersionMutation.mutateAsync,

    isUploading: uploadVersionMutation.isPending,
    isActivating: activateVersionMutation.isPending,
    isCloning: cloneVersionMutation.isPending,
  };
}
