"use client";

import { create } from "zustand";

interface AppState {
  sidebarCollapsed: boolean;
  mobileMenuOpen: boolean;
  toggleSidebar: () => void;
  setSidebarCollapsed: (value: boolean) => void;
  toggleMobileMenu: () => void;
  closeMobileMenu: () => void;
}

/**
 * Global Zustand store for UI state.
 */
export const useAppStore = create<AppState>((set) => ({
  sidebarCollapsed: false,
  mobileMenuOpen: false,

  toggleSidebar: () =>
    set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),

  setSidebarCollapsed: (value: boolean) =>
    set({ sidebarCollapsed: value }),

  toggleMobileMenu: () =>
    set((state) => ({ mobileMenuOpen: !state.mobileMenuOpen })),

  closeMobileMenu: () =>
    set({ mobileMenuOpen: false }),
}));
