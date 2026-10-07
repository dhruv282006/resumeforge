"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { tailoringApi } from "@/lib/api/tailoring";
import type {
  ApplySuggestionsRequest,
  ResumeTailoringJob,
  SuggestionUpdateRequest,
  TailorTriggerRequest,
  TailoringApplyResponse,
  VersionDiffResponse,
} from "@/types/tailoring";

export function useVersionTailoringJobs(versionId?: string) {
  return useQuery<ResumeTailoringJob[]>({
    queryKey: ["tailoring-jobs", versionId],
    queryFn: () => (versionId ? tailoringApi.listVersionTailoringJobs(versionId) : Promise.resolve([])),
    enabled: !!versionId,
  });
}

export function useTailoringJob(jobId?: string, versionId?: string) {
  return useQuery<ResumeTailoringJob>({
    queryKey: ["tailoring-job", jobId],
    queryFn: () => (jobId ? tailoringApi.getTailoringJob(jobId, versionId) : Promise.reject("No job ID")),
    enabled: !!jobId,
  });
}

export function useTailorMutation(versionId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: TailorTriggerRequest) =>
      tailoringApi.triggerTailoring(versionId, payload),
    onSuccess: (newJob) => {
      queryClient.invalidateQueries({ queryKey: ["tailoring-jobs", versionId] });
      queryClient.setQueryData(["tailoring-job", newJob.id], newJob);
    },
  });
}

export function useUpdateSuggestionMutation(jobId?: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      suggestionId,
      payload,
    }: {
      suggestionId: string;
      payload: SuggestionUpdateRequest;
    }) => tailoringApi.updateSuggestion(suggestionId, payload),
    onSuccess: () => {
      if (jobId) {
        queryClient.invalidateQueries({ queryKey: ["tailoring-job", jobId] });
      }
      queryClient.invalidateQueries({ queryKey: ["tailoring-jobs"] });
    },
  });
}

export function useApplySuggestionsMutation(resumeId?: string, versionId?: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: ApplySuggestionsRequest) => {
      if (!versionId) throw new Error("No versionId provided");
      return tailoringApi.applySuggestions(versionId, payload);
    },
    onSuccess: (response: TailoringApplyResponse) => {
      if (resumeId) {
        queryClient.invalidateQueries({ queryKey: ["resumes", resumeId] });
        queryClient.invalidateQueries({ queryKey: ["resume-versions", resumeId] });
      }
      queryClient.invalidateQueries({ queryKey: ["tailoring-jobs"] });
    },
  });
}

export function useVersionDiff(versionId?: string, compareVersionId?: string) {
  return useQuery<VersionDiffResponse>({
    queryKey: ["version-diff", versionId, compareVersionId],
    queryFn: () => {
      if (!versionId || !compareVersionId) {
        return Promise.reject("Both versions required for diff");
      }
      return tailoringApi.getVersionDiff(versionId, compareVersionId);
    },
    enabled: !!versionId && !!compareVersionId,
  });
}
