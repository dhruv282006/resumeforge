"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Menu, LogOut, User, Settings, CheckCircle2 } from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { useAppStore } from "@/lib/stores/app-store";
import { Button } from "@/components/ui/button";

const routeLabels: Record<string, string> = {
  "/dashboard": "Dashboard",
  "/profile": "Master Career Profile",
  "/resumes": "Resumes",
  "/jobs": "Job Descriptions",
  "/applications": "Applications Tracker",
  "/settings": "Account Settings",
};

function getPageTitle(pathname: string): string {
  if (routeLabels[pathname]) return routeLabels[pathname];
  for (const [route, label] of Object.entries(routeLabels)) {
    if (pathname.startsWith(route + "/")) return label;
  }
  return "ResumeForge";
}

export function Topbar() {
  const pathname = usePathname();
  const title = getPageTitle(pathname);
  const { user, logout } = useAuth();
  const { toggleMobileMenu } = useAppStore();
  const [dropdownOpen, setDropdownOpen] = React.useState(false);

  // Close dropdown on click outside
  React.useEffect(() => {
    const handleDocumentClick = () => setDropdownOpen(false);
    if (dropdownOpen) {
      document.addEventListener("click", handleDocumentClick);
    }
    return () => {
      document.removeEventListener("click", handleDocumentClick);
    };
  }, [dropdownOpen]);

  const initials = React.useMemo(() => {
    if (!user?.full_name) return "RF";
    const parts = user.full_name.trim().split(/\s+/);
    if (parts.length === 1) return parts[0].substring(0, 2).toUpperCase();
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
  }, [user?.full_name]);

  return (
    <header className="flex h-14 items-center justify-between border-b bg-card px-4 sm:px-6 z-20">
      <div className="flex items-center gap-3">
        {/* Mobile menu toggle */}
        <button
          onClick={toggleMobileMenu}
          className="flex h-8 w-8 items-center justify-center rounded-lg text-muted-foreground hover:bg-muted hover:text-foreground md:hidden"
          aria-label="Open mobile navigation"
        >
          <Menu className="h-5 w-5" />
        </button>
        <h1 className="text-sm font-semibold text-foreground tracking-tight">{title}</h1>
      </div>

      <div className="flex items-center gap-3">
        {/* User Account Dropdown */}
        <div className="relative" onClick={(e) => e.stopPropagation()}>
          <button
            onClick={() => setDropdownOpen(!dropdownOpen)}
            className="flex items-center gap-2 rounded-full p-1 hover:bg-muted/60 transition-colors focus:outline-none"
            aria-expanded={dropdownOpen}
            aria-label="User account menu"
          >
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-600 text-white text-xs font-semibold select-none shadow-xs">
              {initials}
            </div>
            {user?.full_name && (
              <span className="hidden sm:inline-block text-xs font-medium max-w-[120px] truncate text-foreground">
                {user.full_name.split(" ")[0]}
              </span>
            )}
          </button>

          {dropdownOpen && (
            <div className="absolute right-0 mt-2 w-56 rounded-xl border bg-card p-1.5 shadow-lg z-50 text-xs animate-in fade-in slide-in-from-top-1">
              <div className="p-2 border-b mb-1">
                <p className="font-semibold text-foreground truncate">{user?.full_name || "ResumeForge Candidate"}</p>
                <p className="text-[11px] text-muted-foreground truncate mt-0.5">{user?.email || "candidate@local"}</p>
                {user?.onboarding_completed && (
                  <div className="flex items-center gap-1 text-[10px] text-emerald-600 dark:text-emerald-400 font-medium mt-1">
                    <CheckCircle2 className="h-3 w-3" /> Profile Onboarded
                  </div>
                )}
              </div>

              <Link
                href="/profile"
                onClick={() => setDropdownOpen(false)}
                className="flex items-center gap-2 rounded-lg px-2.5 py-2 text-foreground hover:bg-muted transition-colors"
              >
                <User className="h-3.5 w-3.5 text-muted-foreground" />
                <span>Master Career Profile</span>
              </Link>

              <Link
                href="/settings"
                onClick={() => setDropdownOpen(false)}
                className="flex items-center gap-2 rounded-lg px-2.5 py-2 text-foreground hover:bg-muted transition-colors"
              >
                <Settings className="h-3.5 w-3.5 text-muted-foreground" />
                <span>Account Settings</span>
              </Link>

              <div className="border-t my-1" />

              <button
                onClick={() => {
                  setDropdownOpen(false);
                  logout();
                }}
                className="w-full flex items-center gap-2 rounded-lg px-2.5 py-2 text-destructive hover:bg-destructive/10 transition-colors text-left"
              >
                <LogOut className="h-3.5 w-3.5" />
                <span>Sign Out</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
