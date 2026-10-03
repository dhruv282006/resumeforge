import type { Metadata } from "next";
import Link from "next/link";
import { FileText, Briefcase } from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { EmptyState } from "@/components/shared/empty-state";
import { Button } from "@/components/ui/button";

export const metadata: Metadata = {
  title: "Dashboard",
};

interface StatCardProps {
  label: string;
  value: string | number;
  description: string;
}

function StatCard({ label, value, description }: StatCardProps) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardDescription>{label}</CardDescription>
        <CardTitle className="text-3xl font-bold">{value}</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-xs text-muted-foreground">{description}</p>
      </CardContent>
    </Card>
  );
}

export default function DashboardPage() {
  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-semibold tracking-tight">
          Welcome to ResumeForge
        </h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Your workspace is ready. Start by uploading a resume or analyzing a
          job description.
        </p>
      </div>

      {/* Stat Cards — real zeros, no fake data */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="Resumes"
          value={0}
          description="No resumes uploaded yet"
        />
        <StatCard
          label="Jobs Analyzed"
          value={0}
          description="No job descriptions parsed yet"
        />
        <StatCard
          label="Match Score Avg."
          value="—"
          description="Upload a resume and job to see scores"
        />
        <StatCard
          label="Applications"
          value={0}
          description="No applications tracked yet"
        />
      </div>

      {/* Getting Started */}
      <div className="grid gap-4 lg:grid-cols-2">
        <EmptyState
          icon={FileText}
          title="Upload your first resume"
          description="ResumeForge parses, versions, and stores your resume. Tailor it to any job in seconds."
          action={{ label: "Upload Resume", href: "/resumes/upload" }}
        />
        <EmptyState
          icon={Briefcase}
          title="Analyze your first job description"
          description="Paste a job description to extract requirements and compare them against your resumes."
          action={{ label: "Analyze a Job", href: "/jobs/new" }}
        />
      </div>
    </div>
  );
}
