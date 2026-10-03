"use client";

import * as React from "react";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { useSystemHealth } from "@/lib/hooks/use-system-health";
import { cn } from "@/lib/utils";

interface DotProps {
  status: "healthy" | "degraded" | "unhealthy" | "unknown";
}

function StatusDot({ status }: DotProps) {
  const colorMap = {
    healthy: "bg-emerald-500",
    degraded: "bg-amber-500",
    unhealthy: "bg-red-500",
    unknown: "bg-slate-400",
  };

  const pulseMap = {
    healthy: "animate-pulse",
    degraded: "animate-pulse",
    unhealthy: "animate-pulse",
    unknown: "",
  };

  return (
    <span className="relative flex h-2 w-2 shrink-0" aria-hidden="true">
      <span
        className={cn(
          "absolute inline-flex h-full w-full rounded-full opacity-75",
          colorMap[status],
          pulseMap[status]
        )}
      />
      <span
        className={cn(
          "relative inline-flex h-2 w-2 rounded-full",
          colorMap[status]
        )}
      />
    </span>
  );
}

interface ServiceRowProps {
  name: string;
  status: "ok" | "error";
  latency?: number;
  error?: string;
}

function ServiceRow({ name, status, latency, error }: ServiceRowProps) {
  return (
    <div className="flex items-center justify-between gap-4 text-xs">
      <span className="text-muted-foreground capitalize">{name}</span>
      <div className="flex items-center gap-1.5">
        {status === "ok" ? (
          <>
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
            <span className="text-emerald-600 dark:text-emerald-400">
              {latency !== undefined ? `${latency}ms` : "OK"}
            </span>
          </>
        ) : (
          <>
            <span className="h-1.5 w-1.5 rounded-full bg-red-500" />
            <span className="text-red-600 dark:text-red-400 truncate max-w-[120px]" title={error}>
              {error ?? "Error"}
            </span>
          </>
        )}
      </div>
    </div>
  );
}

export function SystemHealth() {
  const { data, isLoading, isError } = useSystemHealth();

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 px-2 py-1">
        <Skeleton className="h-2 w-2 rounded-full" />
        <Skeleton className="h-3 w-24" />
      </div>
    );
  }

  if (isError || !data) {
    return (
      <TooltipProvider delayDuration={300}>
        <Tooltip>
          <TooltipTrigger asChild>
            <div
              className="flex cursor-default items-center gap-2 rounded px-2 py-1 text-xs text-muted-foreground hover:bg-muted/50 transition-colors"
              aria-label="Backend status: unreachable"
            >
              <StatusDot status="unknown" />
              <span>Backend: Unreachable</span>
            </div>
          </TooltipTrigger>
          <TooltipContent side="top" className="p-3">
            <p className="text-xs text-muted-foreground">
              Could not connect to the API server.
            </p>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    );
  }

  const labelMap = {
    healthy: "Backend: Connected",
    degraded: "Backend: Degraded",
    unhealthy: "Backend: Unhealthy",
  } as const;

  return (
    <TooltipProvider delayDuration={300}>
      <Tooltip>
        <TooltipTrigger asChild>
          <div
            className="flex cursor-default items-center gap-2 rounded px-2 py-1 text-xs text-muted-foreground hover:bg-muted/50 transition-colors"
            aria-label={`Backend status: ${data.status}`}
          >
            <StatusDot status={data.status} />
            <span>{labelMap[data.status]}</span>
          </div>
        </TooltipTrigger>
        <TooltipContent side="top" className="p-3 min-w-[180px]">
          <div className="space-y-2">
            <p className="text-xs font-medium text-foreground mb-2">
              Service Status
            </p>
            <ServiceRow
              name="Database"
              status={data.services.database.status}
              latency={data.services.database.latency_ms}
              error={data.services.database.error}
            />
            <ServiceRow
              name="Redis"
              status={data.services.redis.status}
              latency={data.services.redis.latency_ms}
              error={data.services.redis.error}
            />
            <div className="mt-2 border-t pt-2">
              <p className="text-xs text-muted-foreground">
                v{data.version} · {data.environment}
              </p>
            </div>
          </div>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}
