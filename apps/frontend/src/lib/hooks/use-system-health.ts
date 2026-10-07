"use client";

import { useQuery } from "@tanstack/react-query";
import type { HealthStatus } from "@/types/api";
import { fetchSystemHealth } from "@/lib/api/health";
import { ApiClientError } from "@/lib/api/client";

export interface UseSystemHealthResult {
  data: HealthStatus | undefined;
  isLoading: boolean;
  isError: boolean;
  error: ApiClientError | Error | null;
}

/**
 * TanStack Query hook that polls the backend health endpoint every 30 seconds.
 */
export function useSystemHealth(): UseSystemHealthResult {
  const { data, isLoading, isError, error } = useQuery<
    HealthStatus,
    ApiClientError | Error
  >({
    queryKey: ["system-health"],
    queryFn: fetchSystemHealth,
    refetchInterval: 30_000,
    retry: 3,
    staleTime: 10_000,
  });

  return {
    data,
    isLoading,
    isError,
    error: error ?? null,
  };
}
