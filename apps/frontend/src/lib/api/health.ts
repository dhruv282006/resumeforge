import type { HealthStatus } from "@/types/api";
import { apiClient } from "./client";

/**
 * Fetches the system health status from the backend.
 * Endpoint: GET /api/v1/health
 */
export async function fetchSystemHealth(): Promise<HealthStatus> {
  return apiClient.get<HealthStatus>("/api/v1/health");
}
