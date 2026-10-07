"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { jobsApi } from "@/lib/api/jobs";
import type {
  JobDescription,
  JobCreate,
  JobUpdate,
  JobMatch,
  JobMatchRequest,
  JobRequirement,
} from "@/types/job";

export function useJobs() {
  const queryClient = useQueryClient();

  const query = useQuery<JobDescription[]>({
    queryKey: ["jobs"],
    queryFn: () => jobsApi.getJobs(),
  });

  const createJobMutation = useMutation({
    mutationFn: (payload: JobCreate) => jobsApi.createJob(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["jobs"] });
    },
  });

  const deleteJobMutation = useMutation({
    mutationFn: (id: string) => jobsApi.deleteJob(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["jobs"] });
    },
  });

  return {
    jobs: query.data ?? [],
    isLoading: query.isLoading,
    isError: query.isError,
    refetch: query.refetch,
    createJob: createJobMutation.mutateAsync,
    isCreating: createJobMutation.isPending,
    deleteJob: deleteJobMutation.mutateAsync,
    isDeleting: deleteJobMutation.isPending,
  };
}

export function useJobDetail(jobId: string) {
  const queryClient = useQueryClient();

  const query = useQuery<JobDescription>({
    queryKey: ["jobs", jobId],
    queryFn: () => jobsApi.getJob(jobId),
    enabled: !!jobId,
  });

  const updateJobMutation = useMutation({
    mutationFn: (payload: JobUpdate) => jobsApi.updateJob(jobId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["jobs", jobId] });
      queryClient.invalidateQueries({ queryKey: ["jobs"] });
    },
  });

  const analyzeJobMutation = useMutation({
    mutationFn: () => jobsApi.analyzeJob(jobId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["jobs", jobId] });
      queryClient.invalidateQueries({ queryKey: ["jobs", jobId, "requirements"] });
      queryClient.invalidateQueries({ queryKey: ["jobs"] });
    },
  });

  return {
    job: query.data,
    isLoading: query.isLoading,
    isError: query.isError,
    refetch: query.refetch,
    updateJob: updateJobMutation.mutateAsync,
    isUpdating: updateJobMutation.isPending,
    analyzeJob: analyzeJobMutation.mutateAsync,
    isAnalyzing: analyzeJobMutation.isPending,
  };
}

export function useJobRequirements(
  jobId: string,
  filters?: { category?: string; importance?: string }
) {
  return useQuery<JobRequirement[]>({
    queryKey: ["jobs", jobId, "requirements", filters?.category, filters?.importance],
    queryFn: () => jobsApi.getJobRequirements(jobId, filters),
    enabled: !!jobId,
  });
}

export function useJobMatches(jobId: string) {
  const queryClient = useQueryClient();

  const query = useQuery<JobMatch[]>({
    queryKey: ["jobs", jobId, "matches"],
    queryFn: () => jobsApi.getJobMatches(jobId),
    enabled: !!jobId,
  });

  const matchJobMutation = useMutation({
    mutationFn: (payload: JobMatchRequest) => jobsApi.matchJob(jobId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["jobs", jobId, "matches"] });
    },
  });

  return {
    matches: query.data ?? [],
    isLoading: query.isLoading,
    isError: query.isError,
    refetch: query.refetch,
    runMatch: matchJobMutation.mutateAsync,
    isMatching: matchJobMutation.isPending,
  };
}

export function useJobMatchDetail(jobId: string, matchId: string) {
  return useQuery<JobMatch>({
    queryKey: ["jobs", jobId, "matches", matchId],
    queryFn: () => jobsApi.getJobMatch(jobId, matchId),
    enabled: !!jobId && !!matchId,
  });
}
