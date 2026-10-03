"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  FileText,
  Briefcase,
  ClipboardList,
  Settings,
  User,
  PanelLeftClose,
  PanelLeftOpen,
} from "lucide-react";
import { Separator } from "@/components/ui/separator";
import { SystemHealth } from "@/components/shared/system-health";
import { useAppStore } from "@/lib/stores/app-store";
import { cn } from "@/lib/utils";

interface NavItem {
  label: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
}

const primaryNav: NavItem[] = [
  { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { label: "Master Profile", href: "/profile", icon: User },
  { label: "Resumes", href: "/resumes", icon: FileText },
  { label: "Job Descriptions", href: "/jobs", icon: Briefcase },
  { label: "Applications", href: "/applications", icon: ClipboardList },
];

const secondaryNav: NavItem[] = [
  { label: "Settings", href: "/settings", icon: Settings },
];

interface NavLinkProps {
  item: NavItem;
  collapsed: boolean;
  isActive: boolean;
}

function NavLink({ item, collapsed, isActive }: NavLinkProps) {
  const Icon = item.icon;

  return (
    <Link
      href={item.href}
      aria-label={collapsed ? item.label : undefined}
      aria-current={isActive ? "page" : undefined}
      className={cn(
        "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
        isActive
          ? "bg-accent/10 text-accent"
          : "text-muted-foreground hover:bg-muted hover:text-foreground"
      )}
    >
      <Icon className="h-4 w-4 shrink-0" aria-hidden="true" />
      {!collapsed && (
        <span className="truncate">{item.label}</span>
      )}
    </Link>
  );
}

export function Sidebar() {
  const pathname = usePathname();
  const { sidebarCollapsed, toggleSidebar } = useAppStore();

  return (
    <aside
      className={cn(
        "flex flex-col border-r bg-card transition-all duration-200",
        sidebarCollapsed ? "w-14" : "w-60"
      )}
      aria-label="Main navigation"
    >
      {/* Logo / Wordmark */}
      <div
        className={cn(
          "flex h-14 items-center border-b px-3",
          sidebarCollapsed ? "justify-center" : "justify-between"
        )}
      >
        {!sidebarCollapsed && (
          <Link
            href="/dashboard"
            className="flex items-center gap-2 text-sm font-semibold text-foreground tracking-tight"
          >
            <span className="flex h-6 w-6 items-center justify-center rounded bg-primary text-primary-foreground text-xs font-bold">
              RF
            </span>
            ResumeForge
          </Link>
        )}
        <button
          onClick={toggleSidebar}
          aria-label={sidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
          className="flex h-7 w-7 items-center justify-center rounded-md text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
        >
          {sidebarCollapsed ? (
            <PanelLeftOpen className="h-4 w-4" />
          ) : (
            <PanelLeftClose className="h-4 w-4" />
          )}
        </button>
      </div>

      {/* Primary Navigation */}
      <nav className="flex-1 overflow-y-auto p-2 space-y-0.5">
        {primaryNav.map((item) => (
          <NavLink
            key={item.href}
            item={item}
            collapsed={sidebarCollapsed}
            isActive={pathname === item.href || pathname.startsWith(item.href + "/")}
          />
        ))}

        <Separator className="my-3" />

        {secondaryNav.map((item) => (
          <NavLink
            key={item.href}
            item={item}
            collapsed={sidebarCollapsed}
            isActive={pathname === item.href}
          />
        ))}
      </nav>

      {/* Footer — System Health */}
      <div className={cn("border-t p-2", sidebarCollapsed && "hidden")}>
        <SystemHealth />
      </div>
    </aside>
  );
}
