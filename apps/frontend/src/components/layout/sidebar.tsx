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
  X,
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
  onClick?: () => void;
}

function NavLink({ item, collapsed, isActive, onClick }: NavLinkProps) {
  const Icon = item.icon;

  return (
    <Link
      href={item.href}
      onClick={onClick}
      aria-label={collapsed ? item.label : undefined}
      aria-current={isActive ? "page" : undefined}
      className={cn(
        "flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors",
        isActive
          ? "bg-blue-50 text-blue-700 dark:bg-blue-950/60 dark:text-blue-300 font-semibold shadow-xs"
          : "text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800/60 hover:text-slate-900 dark:hover:text-slate-100"
      )}
    >
      <Icon className={cn("h-4 w-4 shrink-0", isActive && "text-blue-600 dark:text-blue-400")} aria-hidden="true" />
      {!collapsed && (
        <span className="truncate">{item.label}</span>
      )}
    </Link>
  );
}

export function Sidebar() {
  const pathname = usePathname();
  const { sidebarCollapsed, toggleSidebar, mobileMenuOpen, closeMobileMenu } = useAppStore();

  // Close mobile drawer on route change
  React.useEffect(() => {
    closeMobileMenu();
  }, [pathname, closeMobileMenu]);

  return (
    <>
      {/* Mobile Drawer Backdrop */}
      {mobileMenuOpen && (
        <div
          className="fixed inset-0 z-40 bg-slate-900/50 backdrop-blur-xs md:hidden"
          onClick={closeMobileMenu}
          aria-hidden="true"
        />
      )}

      {/* Mobile Drawer */}
      <div
        className={cn(
          "fixed inset-y-0 left-0 z-50 flex w-72 flex-col bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800 transition-transform duration-300 ease-in-out md:hidden shadow-xl",
          mobileMenuOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <div className="flex h-16 items-center justify-between border-b border-slate-100 dark:border-slate-800 px-4">
          <Link
            href="/dashboard"
            onClick={closeMobileMenu}
            className="flex items-center gap-2.5 text-sm font-semibold tracking-tight"
          >
            <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-blue-600 text-white font-bold text-xs">
              RF
            </div>
            <span className="text-base font-bold">ResumeForge</span>
          </Link>
          <button
            onClick={closeMobileMenu}
            className="flex h-8 w-8 items-center justify-center rounded-lg text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800"
            aria-label="Close navigation"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <nav className="flex-1 overflow-y-auto p-3 space-y-1">
          {primaryNav.map((item) => (
            <NavLink
              key={item.href}
              item={item}
              collapsed={false}
              isActive={pathname === item.href || pathname.startsWith(item.href + "/")}
              onClick={closeMobileMenu}
            />
          ))}

          <Separator className="my-3" />

          {secondaryNav.map((item) => (
            <NavLink
              key={item.href}
              item={item}
              collapsed={false}
              isActive={pathname === item.href}
              onClick={closeMobileMenu}
            />
          ))}
        </nav>

        <div className="border-t border-slate-100 dark:border-slate-800 p-3">
          <SystemHealth />
        </div>
      </div>

      {/* Desktop Persistent Sidebar */}
      <aside
        className={cn(
          "hidden md:flex flex-col border-r border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 transition-all duration-200",
          sidebarCollapsed ? "w-16" : "w-64"
        )}
        aria-label="Main desktop navigation"
      >
        {/* Logo / Wordmark */}
        <div
          className={cn(
            "flex h-14 items-center border-b border-slate-100 dark:border-slate-800 px-3",
            sidebarCollapsed ? "justify-center" : "justify-between"
          )}
        >
          {!sidebarCollapsed && (
            <Link
              href="/dashboard"
              className="flex items-center gap-2 text-sm font-semibold tracking-tight"
            >
              <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-blue-600 text-white text-xs font-bold shadow-xs">
                RF
              </span>
              <span className="font-bold text-slate-900 dark:text-slate-100">
                Resume<span className="text-blue-600">Forge</span>
              </span>
            </Link>
          )}
          <button
            onClick={toggleSidebar}
            aria-label={sidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
            className="flex h-8 w-8 items-center justify-center rounded-lg text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-slate-900 transition-colors"
          >
            {sidebarCollapsed ? (
              <PanelLeftOpen className="h-4 w-4" />
            ) : (
              <PanelLeftClose className="h-4 w-4" />
            )}
          </button>
        </div>

        {/* Primary Navigation */}
        <nav className="flex-1 overflow-y-auto p-2.5 space-y-1">
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
        <div className={cn("border-t border-slate-100 dark:border-slate-800 p-2", sidebarCollapsed && "hidden")}>
          <SystemHealth />
        </div>
      </aside>
    </>
  );
}
