"use client";

import * as React from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import {
  ArrowLeft,
  Briefcase,
  Sparkles,
  Layers,
  Sliders,
  CheckCircle2,
  Clock,
  MapPin,
  ExternalLink,
  ChevronRight,
  TrendingUp,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useJobDetail, useJobMatches } from "@/lib/hooks/use-jobs";
import { useResumes } from "@/lib/hooks/use-resumes";
import type { MatchingWeights } from "@/types/job";

export default function JobDetailPage() {
  const params = useParams();
  const router = useRouter();
  const jobId = params?.id as string;

  const { job, isLoading, analyzeJob, isAnalyzing } = useJobDetail(jobId);
  const { matches, runMatch, isMatching } = useJobMatches(jobId);
  const { resumes } = useResumes();

  // Requirements filter
  const [selectedCategory, setSelectedCategory] = React.useState<string>("ALL");
  const [selectedImportance, setSelectedImportance] = React.useState<string>("ALL");

  // Matching configuration state
  const [targetType, setTargetType] = React.useState<"PROFILE" | "RESUME_VERSION">("PROFILE");
  const [selectedResumeVersionId, setSelectedResumeVersionId] = React.useState<string>("");
  const [showWeightsConfig, setShowWeightsConfig] = React.useState(false);
  const [weights, setWeights] = React.useState<MatchingWeights>({
    required_skills: 0.35,
    preferred_skills: 0.15,
    experience_relevance: 0.20,
    project_relevance: 0.15,
    semantic_alignment: 0.15,
  });

  // Extract all available resume versions across all resumes
  const allVersions = React.useMemo(() => {
    return resumes.flatMap((r) =>
      (r.versions || []).map((v) => ({
        ...v,
        resumeTitle: r.title,
      }))
    );
  }, [resumes]);

  const handleRunMatch = async () => {
    try {
      const match = await runMatch({
        target_type: targetType,
        resume_version_id: targetType === "RESUME_VERSION" ? selectedResumeVersionId : null,
        weights: showWeightsConfig ? weights : null,
      });
      if (match?.id) {
        router.push(`/jobs/${jobId}/matches/${match.id}`);
      }
    } catch (err) {
      console.error("Match execution failed:", err);
    }
  };

  const filteredRequirements = React.useMemo(() => {
    if (!job?.requirements) return [];
    return job.requirements.filter((req) => {
      const catMatch = selectedCategory === "ALL" || req.category === selectedCategory;
      const impMatch = selectedImportance === "ALL" || req.importance === selectedImportance;
      return catMatch && impMatch;
    });
  }, [job?.requirements, selectedCategory, selectedImportance]);

  if (isLoading || !job) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-8 w-48 bg-muted rounded" />
        <div className="h-48 bg-muted/40 rounded-lg" />
      </div>
    );
  }

  const isAnalyzed = (job.requirements?.length ?? 0) > 0;

  return (
    <div className="space-y-6">
      {/* Back button & Breadcrumb */}
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Button variant="ghost" size="sm" asChild className="gap-1 px-2">
          <Link href="/jobs">
            <ArrowLeft className="h-4 w-4" />
            Back to Target Jobs
          </Link>
        </Button>
      </div>

      {/* Job Title & Header Card */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between p-6 bg-card border rounded-lg shadow-sm">
        <div className="space-y-1.5">
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold tracking-tight">
              {job.title || "Untitled Job Description"}
            </h1>
            <Badge variant="outline" className="font-medium">
              {job.status}
            </Badge>
          </div>
          <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-muted-foreground">
            {job.company && <span className="font-semibold text-foreground">{job.company}</span>}
            {job.location && (
              <span className="flex items-center gap-1">
                <MapPin className="h-3.5 w-3.5" />
                {job.location}
              </span>
            )}
            {job.employment_type && (
              <span className="flex items-center gap-1">
                <Clock className="h-3.5 w-3.5" />
                {job.employment_type}
              </span>
            )}
            {job.source_url && (
              <a
                href={job.source_url}
                target="_blank"
                rel="noreferrer"
                className="flex items-center gap-1 text-primary hover:underline"
              >
                Original Posting
                <ExternalLink className="h-3 w-3" />
              </a>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button
            onClick={() => analyzeJob()}
            disabled={isAnalyzing}
            variant={isAnalyzed ? "outline" : "default"}
            className="gap-2"
          >
            <Sparkles className="h-4 w-4 text-primary" />
            {isAnalyzing ? "Analyzing JD..." : isAnalyzed ? "Re-Analyze Requirements" : "Analyze Requirements"}
          </Button>
        </div>
      </div>

      {/* Analysis Overview Cards */}
      {isAnalyzed && (
        <div className="grid gap-4 sm:grid-cols-3">
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Extracted Requirements</CardDescription>
              <CardTitle className="text-2xl">{job.requirements?.length ?? 0}</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground">
                Classified into skills, experience, and responsibilities
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Identified Skills</CardDescription>
              <CardTitle className="text-2xl">{job.skills?.length ?? 0}</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground">
                Normalized to canonical industry aliases
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Semantic Matches Run</CardDescription>
              <CardTitle className="text-2xl">{matches.length}</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground">
                Grounded Job Match Score evaluations
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Semantic Match Trigger Section */}
      <Card className="border-primary/20 bg-primary/5">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <CardTitle className="flex items-center gap-2 text-lg">
                <TrendingUp className="h-5 w-5 text-primary" />
                Run Grounded Job Match Analysis
              </CardTitle>
              <CardDescription>
                Compare this job description against candidate evidence to generate a transparent Job Match Score and attribution report.
              </CardDescription>
            </div>
            <Button onClick={handleRunMatch} disabled={isMatching || (targetType === "RESUME_VERSION" && !selectedResumeVersionId)} className="gap-2">
              <Sparkles className="h-4 w-4" />
              {isMatching ? "Computing Match..." : "Run Job Match"}
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <label className="text-xs font-semibold uppercase text-muted-foreground">Matching Target</label>
              <div className="flex gap-2">
                <Button
                  type="button"
                  size="sm"
                  variant={targetType === "PROFILE" ? "default" : "outline"}
                  onClick={() => setTargetType("PROFILE")}
                  className="flex-1"
                >
                  Master Career Profile (Source of Truth)
                </Button>
                <Button
                  type="button"
                  size="sm"
                  variant={targetType === "RESUME_VERSION" ? "default" : "outline"}
                  onClick={() => setTargetType("RESUME_VERSION")}
                  className="flex-1"
                >
                  Specific Resume Version
                </Button>
              </div>
            </div>

            {targetType === "RESUME_VERSION" && (
              <div className="space-y-2">
                <label className="text-xs font-semibold uppercase text-muted-foreground">Select Resume Version</label>
                <select
                  className="w-full h-9 rounded-md border bg-background px-3 text-sm focus:outline-none focus:ring-1 focus:ring-ring"
                  value={selectedResumeVersionId}
                  onChange={(e) => setSelectedResumeVersionId(e.target.value)}
                >
                  <option value="">-- Choose a version --</option>
                  {allVersions.map((v) => (
                    <option key={v.id} value={v.id}>
                      {v.resumeTitle} • v{v.version_number} ({v.change_summary || "Version " + v.version_number})
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>

          {/* Optional Custom Weights Toggle */}
          <div className="border-t pt-3">
            <button
              type="button"
              onClick={() => setShowWeightsConfig(!showWeightsConfig)}
              className="flex items-center gap-1 text-xs font-medium text-muted-foreground hover:text-foreground"
            >
              <Sliders className="h-3.5 w-3.5" />
              {showWeightsConfig ? "Hide Score Weights Configuration" : "Customize Component Weights (Advanced)"}
            </button>

            {showWeightsConfig && (
              <div className="grid gap-3 sm:grid-cols-5 pt-3">
                <div className="space-y-1">
                  <label className="text-xs text-muted-foreground">Required Skills: {Math.round(weights.required_skills * 100)}%</label>
                  <input
                    type="range"
                    min="0.1"
                    max="0.6"
                    step="0.05"
                    className="w-full"
                    value={weights.required_skills}
                    onChange={(e) => setWeights({ ...weights, required_skills: parseFloat(e.target.value) })}
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-xs text-muted-foreground">Preferred Skills: {Math.round(weights.preferred_skills * 100)}%</label>
                  <input
                    type="range"
                    min="0.05"
                    max="0.3"
                    step="0.05"
                    className="w-full"
                    value={weights.preferred_skills}
                    onChange={(e) => setWeights({ ...weights, preferred_skills: parseFloat(e.target.value) })}
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-xs text-muted-foreground">Experience: {Math.round(weights.experience_relevance * 100)}%</label>
                  <input
                    type="range"
                    min="0.1"
                    max="0.4"
                    step="0.05"
                    className="w-full"
                    value={weights.experience_relevance}
                    onChange={(e) => setWeights({ ...weights, experience_relevance: parseFloat(e.target.value) })}
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-xs text-muted-foreground">Projects: {Math.round(weights.project_relevance * 100)}%</label>
                  <input
                    type="range"
                    min="0.05"
                    max="0.3"
                    step="0.05"
                    className="w-full"
                    value={weights.project_relevance}
                    onChange={(e) => setWeights({ ...weights, project_relevance: parseFloat(e.target.value) })}
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-xs text-muted-foreground">Semantic: {Math.round(weights.semantic_alignment * 100)}%</label>
                  <input
                    type="range"
                    min="0.05"
                    max="0.3"
                    step="0.05"
                    className="w-full"
                    value={weights.semantic_alignment}
                    onChange={(e) => setWeights({ ...weights, semantic_alignment: parseFloat(e.target.value) })}
                  />
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Recent Matches */}
      {matches.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Match Analysis Reports</CardTitle>
            <CardDescription>Previous semantic matching evaluations run against this job.</CardDescription>
          </CardHeader>
          <CardContent className="divide-y p-0">
            {matches.map((m) => (
              <div key={m.id} className="flex items-center justify-between p-4 hover:bg-muted/30 transition-colors">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-lg">{m.overall_score}</span>
                    <span className="text-xs text-muted-foreground">/ 100 Job Match Score</span>
                    <Badge variant="outline" className="text-xs">
                      {m.target_type === "PROFILE" ? "Master Profile" : "Resume Version"}
                    </Badge>
                  </div>
                  <div className="text-xs text-muted-foreground flex gap-3">
                    <span>Skills: {m.breakdown_scores?.required_skills}%</span>
                    <span>Experience: {m.breakdown_scores?.experience_relevance}%</span>
                    <span>Projects: {m.breakdown_scores?.project_relevance}%</span>
                    <span>{new Date(m.created_at).toLocaleString()}</span>
                  </div>
                </div>

                <Button variant="ghost" size="sm" asChild className="gap-1">
                  <Link href={`/jobs/${jobId}/matches/${m.id}`}>
                    View Report
                    <ChevronRight className="h-4 w-4" />
                  </Link>
                </Button>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Main Details Tabs */}
      <Tabs defaultValue="requirements" className="space-y-4">
        <TabsList>
          <TabsTrigger value="requirements" className="gap-2">
            <Layers className="h-4 w-4" />
            Requirements ({job.requirements?.length ?? 0})
          </TabsTrigger>
          <TabsTrigger value="skills" className="gap-2">
            <Sparkles className="h-4 w-4" />
            Skills ({job.skills?.length ?? 0})
          </TabsTrigger>
          <TabsTrigger value="raw" className="gap-2">
            <Briefcase className="h-4 w-4" />
            Job Description Text
          </TabsTrigger>
        </TabsList>

        {/* Tab 1: Requirements */}
        <TabsContent value="requirements" className="space-y-4">
          {/* Filters */}
          <div className="flex flex-wrap items-center gap-3 bg-muted/30 p-3 rounded-lg border text-xs">
            <span className="font-semibold text-muted-foreground">Category:</span>
            {["ALL", "SKILL", "EXPERIENCE", "EDUCATION", "RESPONSIBILITY", "CERTIFICATION", "OTHER"].map((cat) => (
              <button
                key={cat}
                type="button"
                onClick={() => setSelectedCategory(cat)}
                className={`px-2.5 py-1 rounded-md font-medium transition-colors ${
                  selectedCategory === cat ? "bg-primary text-primary-foreground" : "bg-card hover:bg-muted text-foreground"
                }`}
              >
                {cat}
              </button>
            ))}

            <span className="font-semibold text-muted-foreground ml-3">Importance:</span>
            {["ALL", "REQUIRED", "PREFERRED"].map((imp) => (
              <button
                key={imp}
                type="button"
                onClick={() => setSelectedImportance(imp)}
                className={`px-2.5 py-1 rounded-md font-medium transition-colors ${
                  selectedImportance === imp ? "bg-primary text-primary-foreground" : "bg-card hover:bg-muted text-foreground"
                }`}
              >
                {imp}
              </button>
            ))}
          </div>

          {filteredRequirements.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground border rounded-lg bg-card">
              No requirements match the selected filters.
            </div>
          ) : (
            <div className="grid gap-3">
              {filteredRequirements.map((req) => (
                <Card key={req.id} className="p-4 flex flex-col gap-2 justify-between">
                  <div className="flex items-start justify-between gap-3">
                    <p className="text-sm font-medium leading-relaxed">{req.text}</p>
                    <div className="flex shrink-0 items-center gap-1.5">
                      <Badge variant="outline" className="text-xs">
                        {req.category}
                      </Badge>
                      <Badge
                        variant="secondary"
                        className={`text-xs ${
                          req.importance === "REQUIRED"
                            ? "bg-red-500/10 text-red-600 border-red-500/20"
                            : "bg-blue-500/10 text-blue-600 border-blue-500/20"
                        }`}
                      >
                        {req.importance}
                      </Badge>
                    </div>
                  </div>

                  <div className="flex flex-wrap items-center gap-3 text-xs text-muted-foreground pt-1 border-t">
                    {req.extracted_skill && <span>Skill: <strong>{req.extracted_skill}</strong></span>}
                    {req.min_experience_years && <span>Min Years: <strong>{req.min_experience_years}+</strong></span>}
                    <span>Confidence: <strong>{Math.round(req.confidence * 100)}%</strong></span>
                    <span>Section: {req.source_section}</span>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        {/* Tab 2: Skills */}
        <TabsContent value="skills" className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-base text-red-600">Required Skills</CardTitle>
                <CardDescription>Mandatory core technical skills identified in the JD.</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {(job.skills || [])
                    .filter((s) => s.importance === "REQUIRED")
                    .map((s) => (
                      <Badge key={s.id} variant="secondary" className="px-3 py-1 bg-red-500/10 text-red-700 border-red-500/20">
                        {s.normalized_skill || s.skill_name}
                      </Badge>
                    ))}
                  {(job.skills || []).filter((s) => s.importance === "REQUIRED").length === 0 && (
                    <span className="text-sm text-muted-foreground">No required skills flagged.</span>
                  )}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-base text-blue-600">Preferred & Bonus Skills</CardTitle>
                <CardDescription>Nice-to-have qualifications and additional tools.</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {(job.skills || [])
                    .filter((s) => s.importance === "PREFERRED")
                    .map((s) => (
                      <Badge key={s.id} variant="secondary" className="px-3 py-1 bg-blue-500/10 text-blue-700 border-blue-500/20">
                        {s.normalized_skill || s.skill_name}
                      </Badge>
                    ))}
                  {(job.skills || []).filter((s) => s.importance === "PREFERRED").length === 0 && (
                    <span className="text-sm text-muted-foreground">No preferred skills flagged.</span>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Tab 3: Raw Job Description */}
        <TabsContent value="raw">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Original Job Posting Text</CardTitle>
            </CardHeader>
            <CardContent>
              <pre className="whitespace-pre-wrap font-sans text-xs bg-muted/40 p-4 rounded-md border leading-relaxed">
                {job.raw_text}
              </pre>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
