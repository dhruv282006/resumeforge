import * as React from "react";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

interface LoadingStateProps {
  rows?: number;
  message?: string;
  className?: string;
}

export function LoadingState({ rows = 3, message, className }: LoadingStateProps) {
  return (
    <div className={cn("space-y-4", className)} aria-label="Loading content">
      {message && (
        <div className="text-sm text-muted-foreground animate-pulse mb-2">{message}</div>
      )}
      {Array.from({ length: rows }).map((_, i) => (
        <div
          key={i}
          className="rounded-lg border bg-card p-6 shadow-sm"
        >
          <div className="flex items-start gap-4">
            <Skeleton className="h-10 w-10 rounded-full shrink-0" />
            <div className="flex-1 space-y-2">
              <Skeleton className="h-4 w-1/3" />
              <Skeleton className="h-3 w-2/3" />
              <Skeleton className="h-3 w-1/2" />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

export function LoadingRow() {
  return (
    <div className="flex items-center gap-4 rounded-lg border bg-card p-4">
      <Skeleton className="h-8 w-8 rounded" />
      <div className="flex-1 space-y-1.5">
        <Skeleton className="h-3.5 w-1/4" />
        <Skeleton className="h-3 w-1/3" />
      </div>
      <Skeleton className="h-6 w-16 rounded-full" />
    </div>
  );
}
