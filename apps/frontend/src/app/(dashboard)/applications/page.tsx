import type { Metadata } from "next";
import { ClipboardList } from "lucide-react";
import { EmptyState } from "@/components/shared/empty-state";

export const metadata: Metadata = {
  title: "Applications",
};

export default function ApplicationsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-semibold tracking-tight">Applications</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Track every application tied to a specific resume version.
        </p>
      </div>

      <EmptyState
        icon={ClipboardList}
        title="No applications tracked"
        description="Link a resume version to a job application to start tracking your progress."
        action={{ label: "Log an Application", href: "/applications/new" }}
      />
    </div>
  );
}
