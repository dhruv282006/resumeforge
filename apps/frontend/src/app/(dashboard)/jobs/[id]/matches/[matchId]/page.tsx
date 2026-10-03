"use client";

import * as React from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  ArrowLeft,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  HelpCircle,
  TrendingUp,
  Award,
  Layers,
  ShieldCheck,
  Building,
  Calendar,
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
import { Progress } from "@/components/ui/progress";
import { useJobDetail, useJobMatchDetail } from "@/lib/hooks/use-jobs";
import type { MatchStatus } from "@/types/job";

export default function MatchDetailPage() {
  const params = useParams();
  const jobId = params?.id as string;
  const matchId = params?.matchId as string;

  const { job } = useJobDetail(jobId);
  const { data: match, isLoading } = useJobMatchDetail(jobId, matchId);

  // Status Filter
  const [statusFilter, setStatusFilter] = React.useState<string>("ALL");

  if (isLoading || !match) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-8 w-48 bg-muted rounded" />
        <div className="h-64 bg-muted/40 rounded-lg" />
      </div>
    );
  }

  // Score tier
  const score = match.overall_score;
  const getScoreTier = (val: number) => {
    if (val >= 80) return { label: "Strong Fit", color: "text-emerald-600", bg: "bg-emerald-500/10 border-emerald-500/20" };
    if (val >= 65) return { label: "Competitive Fit", color: "text-blue-600", bg: "bg-blue-500/10 border-blue-500/20" };
    if (val >= 50) return { label: "Moderate Fit", color: "text-amber-600", bg: "bg-amber-500/10 border-amber-500/20" };
    return { label: "Low Fit", color: "text-red-600", bg: "bg-red-500/10 border-red-500/20" };
  };
  const tier = getScoreTier(score);

  // Count items by status
  const counts = {
    ALL: match.items.length,
    MATCHED: match.items.filter((it) => it.status === "MATCHED").length,
    PARTIAL: match.items.filter((it) => it.status === "PARTIAL").length,
    MISSING: match.items.filter((it) => it.status === "MISSING").length,
    UNKNOWN: match.items.filter((it) => it.status === "UNKNOWN").length,
  };

  const filteredItems = match.items.filter((it) => {
    if (statusFilter === "ALL") return true;
    return it.status === statusFilter;
  });

  const getStatusBadge = (status: MatchStatus) => {
    switch (status) {
      case "MATCHED":
        return (
          <Badge className="gap-1 bg-emerald-500/15 text-emerald-700 hover:bg-emerald-500/25 border-emerald-500/30">
            <CheckCircle2 className="h-3 w-3" />
            Matched
          </Badge>
        );
      case "PARTIAL":
        return (
          <Badge className="gap-1 bg-amber-500/15 text-amber-700 hover:bg-amber-500/25 border-amber-500/30">
            <AlertTriangle className="h-3 w-3" />
            Partial Match
          </Badge>
        );
      case "MISSING":
        return (
          <Badge className="gap-1 bg-red-500/15 text-red-700 hover:bg-red-500/25 border-red-500/30">
            <XCircle className="h-3 w-3" />
            Missing
          </Badge>
        );
      case "UNKNOWN":
        return (
          <Badge variant="outline" className="gap-1 text-muted-foreground">
            <HelpCircle className="h-3 w-3" />
            Unknown
          </Badge>
        );
    }
  };

  const getRequirementText = (reqId: string) => {
    if (!job?.requirements) return "Requirement description unavailable";
    const found = job.requirements.find((r) => r.id === reqId);
    return found ? found.text : "Requirement description unavailable";
  };

  const getRequirementDetails = (reqId: string) => {
    if (!job?.requirements) return null;
    return job.requirements.find((r) => r.id === reqId);
  };

  const breakdown = match.breakdown_scores || {
    required_skills: 0,
    preferred_skills: 0,
    experience_relevance: 0,
    project_relevance: 0,
    semantic_alignment: 0,
  };

  return (
    <div className="space-y-6">
      {/* Back button */}
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Button variant="ghost" size="sm" asChild className="gap-1 px-2">
          <Link href={`/jobs/${jobId}`}>
            <ArrowLeft className="h-4 w-4" />
            Back to Job Details
          </Link>
        </Button>
      </div>

      {/* Header */}
      <div className="flex flex-col gap-2 p-6 bg-card border rounded-lg shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="space-y-1">
            <h1 className="text-2xl font-bold tracking-tight">
              Job Match Analysis Report
            </h1>
            <div className="flex items-center gap-3 text-sm text-muted-foreground">
              <span className="font-semibold text-foreground flex items-center gap-1">
                <Building className="h-4 w-4 text-muted-foreground" />
                {job?.title} • {job?.company || "Target Job"}
              </span>
              <span>•</span>
              <Badge variant="outline" className="text-xs">
                Target: {match.target_type === "PROFILE" ? "Master Career Profile" : "Resume Version"}
              </Badge>
              <span>•</span>
              <span className="flex items-center gap-1 text-xs">
                <Calendar className="h-3.5 w-3.5" />
                {new Date(match.created_at).toLocaleString()}
              </span>
            </div>
          </div>

          <div className={`flex items-center gap-3 px-4 py-2 rounded-lg border ${tier.bg}`}>
            <div className="text-right">
              <div className="text-xs uppercase font-semibold text-muted-foreground">Compatibility</div>
              <div className={`font-bold ${tier.color}`}>{tier.label}</div>
            </div>
            <div className={`text-4xl font-extrabold ${tier.color}`}>
              {match.overall_score}
            </div>
          </div>
        </div>

        {/* Factual Grounding Banner */}
        <div className="mt-4 flex items-center gap-2 rounded-md bg-muted/40 p-3 text-xs text-muted-foreground border">
          <ShieldCheck className="h-4 w-4 text-emerald-600 shrink-0" />
          <span>
            <strong>Transparent & Grounded:</strong> This score is computed from verified candidate profile data, direct skill normalization, and semantic cosine similarity. ResumeForge never invents experience or skills.
          </span>
        </div>
      </div>

      {/* 5-Component Score Breakdown */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <TrendingUp className="h-4 w-4 text-primary" />
            Transparent Score Component Breakdown
          </CardTitle>
          <CardDescription>
            Weighted contribution of each domain component to the final 0–100 Job Match Score.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-5">
          {/* 1. Required Skills */}
          <div className="space-y-1.5">
            <div className="flex justify-between text-xs">
              <span className="font-medium text-foreground">Required Skills Match (Weight: 35%)</span>
              <span className="font-bold">{breakdown.required_skills}%</span>
            </div>
            <Progress value={breakdown.required_skills} className="h-2" />
          </div>

          {/* 2. Preferred Skills */}
          <div className="space-y-1.5">
            <div className="flex justify-between text-xs">
              <span className="font-medium text-foreground">Preferred & Bonus Skills (Weight: 15%)</span>
              <span className="font-bold">{breakdown.preferred_skills}%</span>
            </div>
            <Progress value={breakdown.preferred_skills} className="h-2" />
          </div>

          {/* 3. Experience Relevance */}
          <div className="space-y-1.5">
            <div className="flex justify-between text-xs">
              <span className="font-medium text-foreground">Experience & Career Relevance (Weight: 20%)</span>
              <span className="font-bold">{breakdown.experience_relevance}%</span>
            </div>
            <Progress value={breakdown.experience_relevance} className="h-2" />
          </div>

          {/* 4. Project Relevance */}
          <div className="space-y-1.5">
            <div className="flex justify-between text-xs">
              <span className="font-medium text-foreground">Project Evidence Alignment (Weight: 15%)</span>
              <span className="font-bold">{breakdown.project_relevance}%</span>
            </div>
            <Progress value={breakdown.project_relevance} className="h-2" />
          </div>

          {/* 5. Semantic Alignment */}
          <div className="space-y-1.5">
            <div className="flex justify-between text-xs">
              <span className="font-medium text-foreground">Semantic Conceptual Alignment (Weight: 15%)</span>
              <span className="font-bold">{breakdown.semantic_alignment}%</span>
            </div>
            <Progress value={breakdown.semantic_alignment} className="h-2" />
          </div>
        </CardContent>
      </Card>

      {/* Requirement Breakdown & Evidence Attribution */}
      <div className="space-y-4">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="text-lg font-bold tracking-tight">Requirement Analysis & Grounded Evidence</h2>
            <p className="text-xs text-muted-foreground">
              Every requirement is verified against candidate facts with direct evidence attribution (&quot;WHY?&quot;).
            </p>
          </div>

          {/* Status Filter Pills */}
          <div className="flex flex-wrap gap-1.5 bg-muted/40 p-1.5 rounded-lg border text-xs">
            <button
              onClick={() => setStatusFilter("ALL")}
              className={`px-3 py-1 rounded-md font-medium transition-colors ${
                statusFilter === "ALL" ? "bg-primary text-primary-foreground" : "hover:bg-muted text-muted-foreground"
              }`}
            >
              All ({counts.ALL})
            </button>
            <button
              onClick={() => setStatusFilter("MATCHED")}
              className={`px-3 py-1 rounded-md font-medium transition-colors ${
                statusFilter === "MATCHED" ? "bg-emerald-600 text-white" : "hover:bg-muted text-emerald-700"
              }`}
            >
              Matched ({counts.MATCHED})
            </button>
            <button
              onClick={() => setStatusFilter("PARTIAL")}
              className={`px-3 py-1 rounded-md font-medium transition-colors ${
                statusFilter === "PARTIAL" ? "bg-amber-600 text-white" : "hover:bg-muted text-amber-700"
              }`}
            >
              Partial ({counts.PARTIAL})
            </button>
            <button
              onClick={() => setStatusFilter("MISSING")}
              className={`px-3 py-1 rounded-md font-medium transition-colors ${
                statusFilter === "MISSING" ? "bg-red-600 text-white" : "hover:bg-muted text-red-700"
              }`}
            >
              Missing ({counts.MISSING})
            </button>
            <button
              onClick={() => setStatusFilter("UNKNOWN")}
              className={`px-3 py-1 rounded-md font-medium transition-colors ${
                statusFilter === "UNKNOWN" ? "bg-slate-700 text-white" : "hover:bg-muted text-slate-700"
              }`}
            >
              Unknown ({counts.UNKNOWN})
            </button>
          </div>
        </div>

        {/* Requirements List */}
        {filteredItems.length === 0 ? (
          <div className="text-center py-12 text-muted-foreground border rounded-lg bg-card">
            No requirements match this status filter.
          </div>
        ) : (
          <div className="grid gap-4">
            {filteredItems.map((item) => {
              const reqDetails = getRequirementDetails(item.requirement_id);
              return (
                <Card key={item.id} className="overflow-hidden border">
                  <div className="p-4 space-y-3">
                    {/* Requirement Header */}
                    <div className="flex items-start justify-between gap-4">
                      <div className="space-y-1">
                        <p className="text-sm font-semibold leading-relaxed">
                          {getRequirementText(item.requirement_id)}
                        </p>
                        <div className="flex flex-wrap items-center gap-2 text-xs">
                          {reqDetails && (
                            <>
                              <Badge variant="outline" className="text-xs">
                                {reqDetails.category}
                              </Badge>
                              <Badge
                                variant="secondary"
                                className={`text-xs ${
                                  reqDetails.importance === "REQUIRED"
                                    ? "bg-red-500/10 text-red-600 border-red-500/20"
                                    : "bg-blue-500/10 text-blue-600 border-blue-500/20"
                                }`}
                              >
                                {reqDetails.importance}
                              </Badge>
                              {reqDetails.min_experience_years && (
                                <span className="text-muted-foreground">
                                  Min: {reqDetails.min_experience_years}+ years
                                </span>
                              )}
                            </>
                          )}
                        </div>
                      </div>

                      <div className="shrink-0">{getStatusBadge(item.status)}</div>
                    </div>

                    {/* Evidence Card ("WHY?") */}
                    <div className="bg-muted/30 p-3 rounded-lg border text-xs space-y-2">
                      <div className="flex items-center justify-between text-muted-foreground font-semibold">
                        <span className="uppercase tracking-wider text-[11px]">Attribution & Rationale</span>
                        <span>Confidence: {Math.round(item.score * 100)}%</span>
                      </div>

                      <p className="text-foreground leading-relaxed">
                        {item.explanation || "Evaluation completed based on available candidate profile evidence."}
                      </p>

                      {item.matched_entity_name && (
                        <div className="flex flex-wrap items-center gap-2 pt-1 border-t text-muted-foreground">
                          <span>Matched Source: <strong>{item.matched_entity_name}</strong></span>
                          <span>•</span>
                          <span>Type: {item.matched_entity_type}</span>
                          <span>•</span>
                          <span>Origin: {item.evidence_source}</span>
                        </div>
                      )}

                      {item.evidence_summary && (
                        <p className="text-muted-foreground italic bg-card p-2 rounded border">
                          &ldquo;{item.evidence_summary}&rdquo;
                        </p>
                      )}
                    </div>
                  </div>
                </Card>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
