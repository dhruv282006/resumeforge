import type { Metadata } from "next";
import { FileText } from "lucide-react";
import { EmptyState } from "@/components/shared/empty-state";

export const metadata: Metadata = {
  title: "Resumes",
};

export default function ResumesPage() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-semibold tracking-tight">Resumes</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          All your resume versions in one place.
        </p>
      </div>

      <EmptyState
        icon={FileText}
        title="No resumes yet"
        description="Upload a resume to get started. ResumeForge will parse and version it automatically."
        action={{ label: "Upload Resume", href: "/resumes/upload" }}
      />
    </div>
  );
}
