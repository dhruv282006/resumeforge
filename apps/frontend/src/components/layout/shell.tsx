"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { LayoutDashboard, User, FileText, Briefcase, ClipboardList } from "lucide-react";
import { Sidebar } from "./sidebar";
import { Topbar } from "./topbar";
import { useAuth } from "@/lib/auth-context";
import { cn } from "@/lib/utils";

interface ShellProps {
  children: React.ReactNode;
}

const mobileNavItems = [
  { label: "Home", href: "/dashboard", icon: LayoutDashboard },
  { label: "Profile", href: "/profile", icon: User },
  { label: "Resumes", href: "/resumes", icon: FileText },
  { label: "Jobs", href: "/jobs", icon: Briefcase },
  { label: "Apps", href: "/applications", icon: ClipboardList },
];

export function Shell({ children }: ShellProps) {
  const pathname = usePathname();
  const router = useRouter();
  const { isAuthenticated, isLoading } = useAuth();

  // Route protection
  React.useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push("/login");
    }
  }, [isLoading, isAuthenticated, router]);

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-3">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent" />
          <p className="text-xs text-muted-foreground font-medium">Checking session...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <Topbar />
        <main
          className="flex-1 overflow-y-auto p-4 sm:p-6 pb-20 md:pb-6"
          id="main-content"
          tabIndex={-1}
        >
          {children}
        </main>

        {/* Mobile Bottom Navigation Bar */}
        <nav
          className="fixed bottom-0 left-0 right-0 z-30 flex h-16 border-t border-border bg-card/95 backdrop-blur-md md:hidden"
          aria-label="Mobile bottom navigation"
        >
          <div className="grid h-full w-full grid-cols-5">
            {mobileNavItems.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href || (item.href !== "/dashboard" && pathname.startsWith(item.href));
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "flex flex-col items-center justify-center gap-1 text-[11px] font-medium transition-colors",
                    isActive
                      ? "text-blue-600 dark:text-blue-400 font-semibold"
                      : "text-muted-foreground hover:text-foreground"
                  )}
                >
                  <Icon className={cn("h-5 w-5", isActive ? "stroke-[2.5]" : "stroke-[1.75]")} />
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </div>
        </nav>
      </div>
    </div>
  );
}
