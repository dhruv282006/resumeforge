"use client";

import React, { createContext, useContext, useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { authApi } from "@/lib/api/auth";
import type { LoginPayload, RegisterPayload, User } from "@/types/auth";

interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (payload: LoginPayload) => Promise<void>;
  register: (payload: RegisterPayload) => Promise<void>;
  logout: () => Promise<void>;
  completeOnboarding: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Initialize session from localStorage
  useEffect(() => {
    const initAuth = async () => {
      try {
        const storedToken = localStorage.getItem("resumeforge_token");
        const storedUser = localStorage.getItem("resumeforge_user");

        if (storedToken) {
          setToken(storedToken);
          if (storedUser) {
            try {
              setUser(JSON.parse(storedUser));
            } catch {
              // Ignore invalid JSON in cache
            }
          }
          // Fetch fresh user profile from backend
          try {
            const freshUser = await authApi.getMe();
            setUser(freshUser);
            localStorage.setItem("resumeforge_user", JSON.stringify(freshUser));
          } catch {
            // Token might be expired or invalid
            localStorage.removeItem("resumeforge_token");
            localStorage.removeItem("resumeforge_user");
            setToken(null);
            setUser(null);
          }
        }
      } finally {
        setIsLoading(false);
      }
    };

    initAuth();
  }, []);

  const login = useCallback(
    async (payload: LoginPayload) => {
      const res = await authApi.login(payload);
      setToken(res.access_token);
      setUser(res.user);
      localStorage.setItem("resumeforge_token", res.access_token);
      localStorage.setItem("resumeforge_user", JSON.stringify(res.user));

      if (!res.user.onboarding_completed) {
        router.push("/onboarding");
      } else {
        router.push("/dashboard");
      }
    },
    [router]
  );

  const register = useCallback(
    async (payload: RegisterPayload) => {
      const res = await authApi.register(payload);
      setToken(res.access_token);
      setUser(res.user);
      localStorage.setItem("resumeforge_token", res.access_token);
      localStorage.setItem("resumeforge_user", JSON.stringify(res.user));

      // New users always proceed to guided onboarding
      router.push("/onboarding");
    },
    [router]
  );

  const logout = useCallback(async () => {
    try {
      await authApi.logout();
    } finally {
      localStorage.removeItem("resumeforge_token");
      localStorage.removeItem("resumeforge_user");
      setToken(null);
      setUser(null);
      router.push("/login");
    }
  }, [router]);

  const completeOnboarding = useCallback(async () => {
    try {
      const updatedUser = await authApi.completeOnboarding();
      setUser(updatedUser);
      localStorage.setItem("resumeforge_user", JSON.stringify(updatedUser));
      router.push("/dashboard");
    } catch {
      // In case of error, update local state and proceed to dashboard
      if (user) {
        const fallbackUser = { ...user, onboarding_completed: true };
        setUser(fallbackUser);
        localStorage.setItem("resumeforge_user", JSON.stringify(fallbackUser));
      }
      router.push("/dashboard");
    }
  }, [router, user]);

  const refreshUser = useCallback(async () => {
    try {
      const fresh = await authApi.getMe();
      setUser(fresh);
      localStorage.setItem("resumeforge_user", JSON.stringify(fresh));
    } catch {
      // Ignore
    }
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isLoading,
        isAuthenticated: !!token && !!user,
        login,
        register,
        logout,
        completeOnboarding,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
