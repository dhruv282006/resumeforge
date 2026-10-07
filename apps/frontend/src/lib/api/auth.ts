import { apiClient } from "./client";
import type { AuthResponse, LoginPayload, RegisterPayload, User } from "@/types/auth";

export const authApi = {
  async register(payload: RegisterPayload): Promise<AuthResponse> {
    return apiClient.post<AuthResponse>("/api/v1/auth/register", payload);
  },

  async login(payload: LoginPayload): Promise<AuthResponse> {
    return apiClient.post<AuthResponse>("/api/v1/auth/login", payload);
  },

  async getMe(): Promise<User> {
    return apiClient.get<User>("/api/v1/auth/me");
  },

  async logout(): Promise<void> {
    try {
      await apiClient.post("/api/v1/auth/logout");
    } catch {
      // Ignore network errors on logout
    }
  },

  async completeOnboarding(): Promise<User> {
    return apiClient.post<User>("/api/v1/auth/onboarding/complete", {
      onboarding_completed: true,
    });
  },
};
