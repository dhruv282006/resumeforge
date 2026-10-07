"use client";

import * as React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowLeft, Sparkles, Briefcase, AlertCircle, Building2, MapPin, Globe } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { useJobs } from "@/lib/hooks/use-jobs";
import { jobsApi } from "@/lib/api/jobs";
import { toast } from "sonner";

export default function NewJobPage() {
  const router = useRouter();
  const { createJob, isCreating } = useJobs();

  const [title, setTitle] = React.useState("");
  const [company, setCompany] = React.useState("");
  const [location, setLocation] = React.useState("");
  const [employmentType, setEmploymentType] = React.useState("Full-time");
  const [sourceUrl, setSourceUrl] = React.useState("");
  const [rawText, setRawText] = React.useState("");
  const [isAnalyzing, setIsAnalyzing] = React.useState(false);
  const [errorMessage, setErrorMessage] = React.useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !rawText.trim()) {
      setErrorMessage("Please provide a Job Title and the Job Description text.");
      return;
    }

    setIsAnalyzing(true);
    setErrorMessage(null);

    try {
      // 1. Create the job record
      const job = await createJob({
        title: title.trim(),
        company: company.trim() || undefined,
        location: location.trim() || undefined,
        employment_type: employmentType.trim() || undefined,
        source_url: sourceUrl.trim() || undefined,
        raw_text: rawText.trim(),
      });

      toast.info("Job created. Analyzing requirements with NLP pipeline...");

      // 2. Trigger analysis
      try {
        await jobsApi.analyzeJob(job.id);
        toast.success(`Job "${job.title}" analyzed successfully!`);
      } catch (analyzeErr) {
        console.warn("Analysis had an issue, but job was saved:", analyzeErr);
        toast.warning("Job saved. You can re-run analysis anytime.");
      }

      // 3. Navigate to job detail page
      router.push(`/jobs/${job.id}`);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to create and analyze job description.";
      setErrorMessage(msg);
      toast.error(msg);
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Back button */}
      <div>
        <Button variant="ghost" size="sm" asChild className="mb-2 -ml-2 text-xs">
          <Link href="/jobs">
            <ArrowLeft className="h-3.5 w-3.5 mr-1" /> Back to Target Jobs
          </Link>
        </Button>
        <h1 className="text-2xl font-bold tracking-tight">Analyze Job Description</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Paste a target job posting. ResumeForge extracts explicit skills, experience levels, and requirements to enable transparent matching.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Job Details Card */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Briefcase className="h-4 w-4 text-primary" /> Role Information
            </CardTitle>
            <CardDescription className="text-xs">
              Basic metadata about the target role and company.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-1">
                <label className="text-xs font-medium">Job Title *</label>
                <Input
                  placeholder="e.g. Senior Backend Engineer"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  required
                />
              </div>

              <div className="space-y-1">
                <label className="text-xs font-medium">Company Name</label>
                <Input
                  placeholder="e.g. Stripe, OpenAI, Microsoft"
                  value={company}
                  onChange={(e) => setCompany(e.target.value)}
                />
              </div>

              <div className="space-y-1">
                <label className="text-xs font-medium">Location</label>
                <Input
                  placeholder="e.g. Remote, San Francisco, CA"
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                />
              </div>

              <div className="space-y-1">
                <label className="text-xs font-medium">Employment Type</label>
                <Input
                  placeholder="e.g. Full-time, Contract"
                  value={employmentType}
                  onChange={(e) => setEmploymentType(e.target.value)}
                />
              </div>
            </div>

            <div className="space-y-1">
              <label className="text-xs font-medium">Job Posting URL (Optional)</label>
              <Input
                placeholder="https://linkedin.com/jobs/view/... or company career link"
                value={sourceUrl}
                onChange={(e) => setSourceUrl(e.target.value)}
              />
            </div>
          </CardContent>
        </Card>

        {/* Job Description Text Card */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-primary" /> Job Description Content *
            </CardTitle>
            <CardDescription className="text-xs">
              Paste the complete text of the job description including responsibilities, requirements, and preferred qualifications.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <Textarea
              rows={12}
              placeholder="Paste job description here... (e.g. About the role, Responsibilities, Requirements, Nice to have...)"
              value={rawText}
              onChange={(e) => setRawText(e.target.value)}
              required
              className="font-mono text-xs leading-relaxed"
            />

            {errorMessage && (
              <div className="p-3 rounded-lg bg-destructive/10 text-destructive text-xs flex items-center gap-2">
                <AlertCircle className="h-4 w-4 shrink-0" />
                <span>{errorMessage}</span>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Submit Actions */}
        <div className="flex items-center justify-end gap-3">
          <Button variant="outline" asChild disabled={isAnalyzing}>
            <Link href="/jobs">Cancel</Link>
          </Button>
          <Button type="submit" disabled={isAnalyzing || isCreating || !title.trim() || !rawText.trim()}>
            <Sparkles className="h-4 w-4 mr-1.5" />
            {isAnalyzing ? "Extracting Requirements..." : "Create & Analyze Requirements"}
          </Button>
        </div>
      </form>
    </div>
  );
}
