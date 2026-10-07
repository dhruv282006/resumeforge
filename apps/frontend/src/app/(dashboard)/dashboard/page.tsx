"use client";

import Link from "next/link";
import {
  FileText,
  Briefcase,
  ClipboardList,
  CheckCircle2,
  ArrowRight,
  Upload,
  Sparkles,
  TrendingUp,
  PlusCircle,
  Clock,
} from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { useAuth } from "@/lib/auth-context";
import { useResumes } from "@/lib/hooks/use-resumes";
import { useJobs } from "@/lib/hooks/use-jobs";
import { useApplications } from "@/lib/hooks/use-applications";
import { useProfile } from "@/lib/hooks/use-profile";

export default function DashboardPage() {
  const { user } = useAuth();
  const { resumes, isLoading: loadingResumes } = useResumes();
  const { jobs, isLoading: loadingJobs } = useJobs();
  const { applications, stats: appStats, isLoading: loadingApps } = useApplications();
  const { profile, completeness, isLoading: loadingProfile } = useProfile();

  const resumeCount = resumes.length;
  const jobCount = jobs.length;
  const appCount = applications.length;
  const activeOffers = appStats?.offered ?? 0;
  const interviewingCount = appStats?.interviewing ?? 0;
  const overallCompleteness = completeness?.overall ?? (profile?.headline ? 65 : 25);

  const firstName = user?.full_name?.split(" ")[0] || profile?.full_name?.split(" ")[0] || "Candidate";

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
            Welcome back, {firstName} 👋
          </h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Here is what is happening across your resumes, target jobs, and applications.
          </p>
        </div>
        <div className="flex items-center gap-2.5">
          <Link href="/resumes/upload">
            <Button variant="outline" size="sm" className="gap-1.5 h-9 rounded-xl border-slate-300 dark:border-slate-700">
              <Upload className="h-4 w-4" />
              Upload Resume
            </Button>
          </Link>
          <Link href="/jobs/new">
            <Button size="sm" className="gap-1.5 h-9 bg-blue-600 hover:bg-blue-700 text-white rounded-xl shadow-xs">
              <Sparkles className="h-4 w-4" />
              Analyze Target Job
            </Button>
          </Link>
        </div>
      </div>

      {/* Smart Next-Step Guide */}
      <div className="rounded-2xl border border-blue-200 dark:border-blue-900/60 bg-blue-50/60 dark:bg-blue-950/30 p-5 sm:p-6 shadow-xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1.5">
            <div className="flex items-center gap-2">
              <span className="flex h-5 w-5 items-center justify-center rounded-full bg-blue-600 text-white text-xs font-bold">
                ✓
              </span>
              <h3 className="font-semibold text-sm sm:text-base text-slate-900 dark:text-slate-100">
                Continue where you left off
              </h3>
            </div>
            <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-400">
              {resumeCount === 0
                ? "You haven't added a resume yet. Upload your existing PDF or build one from your profile."
                : jobCount === 0
                ? "You have a master resume! Now paste a target job description to compute your match score."
                : "You have target jobs on file. Run tailoring to generate grounded ATS-ready bullet points."}
            </p>
          </div>
          <div>
            {resumeCount === 0 ? (
              <Link href="/resumes/upload">
                <Button size="sm" className="bg-blue-600 hover:bg-blue-700 text-white rounded-xl gap-1.5 shadow-xs">
                  Upload Resume <ArrowRight className="h-3.5 w-3.5" />
                </Button>
              </Link>
            ) : jobCount === 0 ? (
              <Link href="/jobs/new">
                <Button size="sm" className="bg-blue-600 hover:bg-blue-700 text-white rounded-xl gap-1.5 shadow-xs">
                  Analyze a Job <ArrowRight className="h-3.5 w-3.5" />
                </Button>
              </Link>
            ) : (
              <Link href="/jobs">
                <Button size="sm" className="bg-blue-600 hover:bg-blue-700 text-white rounded-xl gap-1.5 shadow-xs">
                  View Job Matches <ArrowRight className="h-3.5 w-3.5" />
                </Button>
              </Link>
            )}
          </div>
        </div>
      </div>

      {/* 4 High-Level Metrics Cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {/* Profile Strength */}
        <Card className="border-slate-200 dark:border-slate-800 shadow-xs">
          <CardHeader className="pb-2">
            <CardDescription className="flex items-center justify-between text-xs">
              <span>Profile Strength</span>
              <CheckCircle2 className="h-4 w-4 text-blue-600" />
            </CardDescription>
            <CardTitle className="text-3xl font-bold tracking-tight">
              {overallCompleteness}%
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <Progress value={overallCompleteness} className="h-1.5" />
            <p className="text-[11px] text-slate-500">
              {overallCompleteness >= 80 ? "Well-documented career profile" : "Add skills & projects to reach 100%"}
            </p>
          </CardContent>
        </Card>

        {/* Resumes */}
        <Card className="border-slate-200 dark:border-slate-800 shadow-xs">
          <CardHeader className="pb-2">
            <CardDescription className="flex items-center justify-between text-xs">
              <span>Resumes Created</span>
              <FileText className="h-4 w-4 text-indigo-600" />
            </CardDescription>
            <CardTitle className="text-3xl font-bold tracking-tight">
              {loadingResumes ? "-" : resumeCount}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-[11px] text-slate-500">
              {resumeCount === 0
                ? "No resumes created yet"
                : `${resumeCount} version-controlled resume${resumeCount > 1 ? "s" : ""}`}
            </p>
          </CardContent>
        </Card>

        {/* Jobs Analyzed */}
        <Card className="border-slate-200 dark:border-slate-800 shadow-xs">
          <CardHeader className="pb-2">
            <CardDescription className="flex items-center justify-between text-xs">
              <span>Jobs Analyzed</span>
              <Briefcase className="h-4 w-4 text-emerald-600" />
            </CardDescription>
            <CardTitle className="text-3xl font-bold tracking-tight">
              {loadingJobs ? "-" : jobCount}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-[11px] text-slate-500">
              {jobCount === 0
                ? "0 job postings analyzed"
                : `${jobCount} target job${jobCount > 1 ? "s" : ""} on file`}
            </p>
          </CardContent>
        </Card>

        {/* Applications */}
        <Card className="border-slate-200 dark:border-slate-800 shadow-xs">
          <CardHeader className="pb-2">
            <CardDescription className="flex items-center justify-between text-xs">
              <span>Active Applications</span>
              <ClipboardList className="h-4 w-4 text-amber-600" />
            </CardDescription>
            <CardTitle className="text-3xl font-bold tracking-tight">
              {loadingApps ? "-" : appCount}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-[11px] text-slate-500">
              {interviewingCount > 0
                ? `${interviewingCount} in interview stages`
                : `${activeOffers} offer${activeOffers === 1 ? "" : "s"} received`}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Quick Action Sections */}
      <div className="grid gap-6 md:grid-cols-2">
        {/* Recent Resumes */}
        <Card className="border-slate-200 dark:border-slate-800 shadow-xs">
          <CardHeader className="flex flex-row items-center justify-between pb-3">
            <div>
              <CardTitle className="text-base font-semibold">Your Resumes</CardTitle>
              <CardDescription className="text-xs">Version-controlled resumes & branches</CardDescription>
            </div>
            <Link href="/resumes">
              <Button variant="ghost" size="sm" className="text-xs gap-1 text-slate-500 hover:text-slate-900">
                View All <ArrowRight className="h-3.5 w-3.5" />
              </Button>
            </Link>
          </CardHeader>
          <CardContent>
            {resumes.length === 0 ? (
              <div className="text-center py-8 border border-dashed border-slate-200 dark:border-slate-800 rounded-xl space-y-2.5">
                <FileText className="h-8 w-8 text-slate-400 mx-auto" />
                <p className="text-xs text-slate-500">No resumes created or uploaded yet.</p>
                <Link href="/resumes/upload">
                  <Button size="sm" variant="outline" className="text-xs rounded-lg">
                    Upload Your First Resume
                  </Button>
                </Link>
              </div>
            ) : (
              <div className="space-y-2.5">
                {resumes.slice(0, 3).map((r) => (
                  <Link
                    key={r.id}
                    href={`/resumes/${r.id}`}
                    className="flex items-center justify-between p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 hover:border-blue-300 dark:hover:border-blue-700 bg-white dark:bg-slate-900 transition-all shadow-2xs"
                  >
                    <div>
                      <h4 className="text-sm font-semibold text-slate-900 dark:text-slate-100">{r.title}</h4>
                      <p className="text-xs text-slate-500">
                        {r.target_role || "General"} • {r.versions?.length || 1} version{(r.versions?.length || 1) > 1 ? "s" : ""}
                      </p>
                    </div>
                    <Badge variant="outline" className="text-xs font-mono">
                      v{r.versions?.[0]?.version_number || "1.0"}
                    </Badge>
                  </Link>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Recent Jobs */}
        <Card className="border-slate-200 dark:border-slate-800 shadow-xs">
          <CardHeader className="flex flex-row items-center justify-between pb-3">
            <div>
              <CardTitle className="text-base font-semibold">Target Jobs</CardTitle>
              <CardDescription className="text-xs">Parsed requirements & match analyses</CardDescription>
            </div>
            <Link href="/jobs">
              <Button variant="ghost" size="sm" className="text-xs gap-1 text-slate-500 hover:text-slate-900">
                View All <ArrowRight className="h-3.5 w-3.5" />
              </Button>
            </Link>
          </CardHeader>
          <CardContent>
            {jobs.length === 0 ? (
              <div className="text-center py-8 border border-dashed border-slate-200 dark:border-slate-800 rounded-xl space-y-2.5">
                <Briefcase className="h-8 w-8 text-slate-400 mx-auto" />
                <p className="text-xs text-slate-500">No job postings analyzed yet.</p>
                <Link href="/jobs/new">
                  <Button size="sm" variant="outline" className="text-xs rounded-lg">
                    Analyze a Target Job
                  </Button>
                </Link>
              </div>
            ) : (
              <div className="space-y-2.5">
                {jobs.slice(0, 3).map((j) => (
                  <Link
                    key={j.id}
                    href={`/jobs/${j.id}`}
                    className="flex items-center justify-between p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 hover:border-blue-300 dark:hover:border-blue-700 bg-white dark:bg-slate-900 transition-all shadow-2xs"
                  >
                    <div>
                      <h4 className="text-sm font-semibold text-slate-900 dark:text-slate-100">{j.title}</h4>
                      <p className="text-xs text-slate-500">{j.company || "Target Company"}</p>
                    </div>
                    <div className="flex items-center gap-1 text-xs text-slate-400 font-mono">
                      <Clock className="h-3 w-3" />
                      {new Date(j.created_at).toLocaleDateString()}
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
