"use client";

import * as React from "react";
import { usePathname } from "next/navigation";

const routeLabels: Record<string, string> = {
  "/dashboard": "Dashboard",
  "/resumes": "Resumes",
  "/jobs": "Job Descriptions",
  "/applications": "Applications",
  "/settings": "Settings",
};

function getPageTitle(pathname: string): string {
  // Exact match
  if (routeLabels[pathname]) return routeLabels[pathname];

  // Prefix match for nested routes
  for (const [route, label] of Object.entries(routeLabels)) {
    if (pathname.startsWith(route + "/")) return label;
  }

  return "ResumeForge";
}

function UserAvatar() {
  // Placeholder: initials-based avatar — no auth yet
  return (
    <div
      aria-label="User account"
      className="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-primary-foreground text-xs font-semibold select-none"
    >
      RF
    </div>
  );
}

export function Topbar() {
  const pathname = usePathname();
  const title = getPageTitle(pathname);

  return (
    <header className="flex h-14 items-center justify-between border-b bg-card px-6">
      <h1 className="text-sm font-semibold text-foreground">{title}</h1>
      <div className="flex items-center gap-3">
        <UserAvatar />
      </div>
    </header>
  );
}
