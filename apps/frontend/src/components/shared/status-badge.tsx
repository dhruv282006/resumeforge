import * as React from "react";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

type StatusVariant = "ok" | "error" | "warning" | "unknown";

interface StatusBadgeProps {
  status: StatusVariant;
  label?: string;
  className?: string;
}

const statusConfig: Record<
  StatusVariant,
  { label: string; dotClass: string; badgeVariant: "default" | "secondary" | "destructive" | "outline" }
> = {
  ok: {
    label: "OK",
    dotClass: "bg-emerald-500",
    badgeVariant: "secondary",
  },
  error: {
    label: "Error",
    dotClass: "bg-red-500",
    badgeVariant: "destructive",
  },
  warning: {
    label: "Degraded",
    dotClass: "bg-amber-500",
    badgeVariant: "outline",
  },
  unknown: {
    label: "Unknown",
    dotClass: "bg-slate-400",
    badgeVariant: "outline",
  },
};

export function StatusBadge({ status, label, className }: StatusBadgeProps) {
  const config = statusConfig[status];

  return (
    <Badge
      variant={config.badgeVariant}
      className={cn("gap-1.5 font-medium", className)}
    >
      <span
        className={cn("h-1.5 w-1.5 rounded-full shrink-0", config.dotClass)}
        aria-hidden="true"
      />
      {label ?? config.label}
    </Badge>
  );
}
