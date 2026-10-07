"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { applicationsApi } from "@/lib/api/applications";
import type {
  ApplicationItem,
  ApplicationStats,
  CreateApplicationPayload,
  UpdateApplicationPayload,
} from "@/types/application";

export function useApplications(statusFilter?: string) {
  const queryClient = useQueryClient();

  const query = useQuery<ApplicationItem[]>({
    queryKey: ["applications", statusFilter],
    queryFn: () => applicationsApi.getApplications(statusFilter),
  });

  const statsQuery = useQuery<ApplicationStats>({
    queryKey: ["applications", "stats"],
    queryFn: () => applicationsApi.getStats(),
  });

  const createMutation = useMutation({
    mutationFn: (payload: CreateApplicationPayload) =>
      applicationsApi.createApplication(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["applications"] });
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: UpdateApplicationPayload }) =>
      applicationsApi.updateApplication(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["applications"] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => applicationsApi.deleteApplication(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["applications"] });
    },
  });

  return {
    applications: query.data ?? [],
    stats: statsQuery.data,
    isLoading: query.isLoading || statsQuery.isLoading,
    isError: query.isError,
    refetch: () => {
      query.refetch();
      statsQuery.refetch();
    },
    createApplication: createMutation.mutateAsync,
    isCreating: createMutation.isPending,
    updateApplication: updateMutation.mutateAsync,
    isUpdating: updateMutation.isPending,
    deleteApplication: deleteMutation.mutateAsync,
    isDeleting: deleteMutation.isPending,
  };
}
