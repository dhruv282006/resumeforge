export interface HealthStatus {
  status: "healthy" | "degraded" | "unhealthy";
  version: string;
  environment: string;
  timestamp: string;
  services: {
    database: ServiceStatus;
    redis: ServiceStatus;
  };
}

export interface ServiceStatus {
  status: "ok" | "error";
  latency_ms?: number;
  error?: string;
}

export interface ApiError {
  error: string;
  message: string;
  detail?: unknown;
}

export interface ApiResponse<T> {
  data: T;
  success: boolean;
}

export interface Resume {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  version: number;
}

export interface JobDescription {
  id: string;
  title: string;
  company: string;
  created_at: string;
  updated_at: string;
}

export interface Application {
  id: string;
  resume_id: string;
  job_id: string;
  status: "applied" | "interviewing" | "offered" | "rejected" | "withdrawn";
  applied_at: string;
  updated_at: string;
}
