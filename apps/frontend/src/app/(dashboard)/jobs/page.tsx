import type { Metadata } from "next";
import { Briefcase } from "lucide-react";
import { EmptyState } from "@/components/shared/empty-state";

export const metadata: Metadata = {
  title: "Job Descriptions",
};

export default function JobsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-semibold tracking-tight">
          Job Descriptions
        </h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Analyze job descriptions and match them against your resumes.
        </p>
      </div>

      <EmptyState
        icon={Briefcase}
        title="No job descriptions analyzed"
        description="Paste or upload a job description to analyze requirements and match it against your resumes."
        action={{ label: "Analyze a Job", href: "/jobs/new" }}
      />
    </div>
  );
}
