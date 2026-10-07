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
  Sparkles,
  ShieldCheck,
  Building,
  ChevronDown,
  ChevronUp,
  Plus,
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

  // Status Filter: "ALL" | "MATCHED" | "PARTIAL" | "MISSING"
  const [activeTab, setActiveTab] = React.useState<string>("ALL");
  const [showTechnicalBreakdown, setShowTechnicalBreakdown] = React.useState<boolean>(false);
  const [expandedEvidenceIds, setExpandedEvidenceIds] = React.useState<Record<string, boolean>>({});

  const toggleEvidence = (id: string) => {
    setExpandedEvidenceIds((prev) => ({
      ...prev,
      [id]: !prev[id],
    }));
  };

  if (isLoading || !match) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-8 w-48 bg-muted rounded" />
        <div className="h-64 bg-muted/40 rounded-xl" />
      </div>
    );
  }

  const score = Math.round(match.overall_score);

  const getScoreInfo = (val: number) => {
    if (val >= 80) {
      return {
        label: "Strong Match",
        summary: "Your skills and experience align closely with what this employer needs.",
        badgeClass: "bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/60 dark:text-emerald-300 dark:border-emerald-800",
        ringClass: "text-emerald-600",
      };
    }
    if (val >= 65) {
      return {
        label: "Competitive Match",
        summary: "You meet the core requirements. A targeted resume version will boost your chances.",
        badgeClass: "bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-950/60 dark:text-blue-300 dark:border-blue-800",
        ringClass: "text-blue-600",
      };
    }
    if (val >= 50) {
      return {
        label: "Moderate Match",
        summary: "You have several relevant skills, but a few key requirements are missing or unphrased.",
        badgeClass: "bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/60 dark:text-amber-300 dark:border-amber-800",
        ringClass: "text-amber-600",
      };
    }
    return {
      label: "Needs Improvement",
      summary: "Significant experience gaps detected. Consider adding matching projects or coursework.",
      badgeClass: "bg-rose-50 text-rose-700 border-rose-200 dark:bg-rose-950/60 dark:text-rose-300 dark:border-rose-800",
      ringClass: "text-rose-600",
    };
  };

  const scoreInfo = getScoreInfo(score);

  // Bucket counts
  const matchedCount = match.items.filter((it) => it.status === "MATCHED").length;
  const partialCount = match.items.filter((it) => it.status === "PARTIAL").length;
  const missingCount = match.items.filter((it) => it.status === "MISSING").length;

  const filteredItems = match.items.filter((it) => {
    if (activeTab === "ALL") return true;
    return it.status === activeTab;
  });

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
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Back button */}
      <div className="flex items-center gap-2">
        <Button variant="ghost" size="sm" asChild className="gap-1.5 px-2 text-slate-500 hover:text-slate-800">
          <Link href={`/jobs/${jobId}`}>
            <ArrowLeft className="h-4 w-4" />
            Back to Job Details
          </Link>
        </Button>
      </div>

      {/* Hero Match Score Card */}
      <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 sm:p-8 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-3 flex-1">
            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-slate-500">
              <Building className="h-4 w-4 text-slate-400" />
              <span>{job?.company || "Target Company"}</span>
              <span>•</span>
              <span className="text-slate-700 dark:text-slate-300">{job?.title}</span>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight">
                {score}% Match
              </h1>
              <Badge className={`px-3 py-1 text-xs font-semibold rounded-full border ${scoreInfo.badgeClass}`}>
                {scoreInfo.label}
              </Badge>
            </div>

            <p className="text-sm text-slate-600 dark:text-slate-400 max-w-2xl leading-relaxed">
              {scoreInfo.summary}
            </p>

            {/* Quick CTAs */}
            <div className="pt-2 flex flex-wrap items-center gap-3">
              <Link href={`/resumes?tailorForJob=${jobId}`}>
                <Button className="h-10 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-xl gap-2 shadow-sm">
                  <Sparkles className="h-4 w-4" />
                  Tailor My Resume for This Job
                </Button>
              </Link>
              <Link href={`/applications`}>
                <Button variant="outline" className="h-10 rounded-xl gap-1.5 border-slate-300 dark:border-slate-700">
                  <Plus className="h-4 w-4" />
                  Track in Applications
                </Button>
              </Link>
            </div>
          </div>

          {/* 3 Outcome Summary Cards */}
          <div className="grid grid-cols-3 gap-3 md:w-80 shrink-0">
            <div
              onClick={() => setActiveTab("MATCHED")}
              className={`p-3.5 rounded-xl border cursor-pointer transition-all ${
                activeTab === "MATCHED"
                  ? "border-emerald-500 bg-emerald-50/80 dark:bg-emerald-950/40 ring-2 ring-emerald-500/20"
                  : "border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/60 hover:border-emerald-300"
              }`}
            >
              <div className="flex items-center gap-1.5 text-xs font-semibold text-emerald-700 dark:text-emerald-400">
                <CheckCircle2 className="h-3.5 w-3.5" />
                <span>Matched</span>
              </div>
              <div className="mt-1 text-2xl font-bold text-slate-900 dark:text-slate-100">
                {matchedCount}
              </div>
              <div className="text-[11px] text-slate-500">Skills present</div>
            </div>

            <div
              onClick={() => setActiveTab("PARTIAL")}
              className={`p-3.5 rounded-xl border cursor-pointer transition-all ${
                activeTab === "PARTIAL"
                  ? "border-amber-500 bg-amber-50/80 dark:bg-amber-950/40 ring-2 ring-amber-500/20"
                  : "border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/60 hover:border-amber-300"
              }`}
            >
              <div className="flex items-center gap-1.5 text-xs font-semibold text-amber-700 dark:text-amber-400">
                <AlertTriangle className="h-3.5 w-3.5" />
                <span>Partial</span>
              </div>
              <div className="mt-1 text-2xl font-bold text-slate-900 dark:text-slate-100">
                {partialCount}
              </div>
              <div className="text-[11px] text-slate-500">Needs highlight</div>
            </div>

            <div
              onClick={() => setActiveTab("MISSING")}
              className={`p-3.5 rounded-xl border cursor-pointer transition-all ${
                activeTab === "MISSING"
                  ? "border-rose-500 bg-rose-50/80 dark:bg-rose-950/40 ring-2 ring-rose-500/20"
                  : "border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/60 hover:border-rose-300"
              }`}
            >
              <div className="flex items-center gap-1.5 text-xs font-semibold text-rose-700 dark:text-rose-400">
                <XCircle className="h-3.5 w-3.5" />
                <span>Missing</span>
              </div>
              <div className="mt-1 text-2xl font-bold text-slate-900 dark:text-slate-100">
                {missingCount}
              </div>
              <div className="text-[11px] text-slate-500">Not found</div>
            </div>
          </div>
        </div>
      </div>

      {/* Progressive Disclosure: Collapsible Technical Breakdown */}
      <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/40 overflow-hidden">
        <button
          onClick={() => setShowTechnicalBreakdown(!showTechnicalBreakdown)}
          className="w-full flex items-center justify-between p-4 text-xs font-semibold text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800/60 transition-colors"
        >
          <div className="flex items-center gap-2">
            <TrendingUp className="h-4 w-4 text-blue-600" />
            <span>How was this score calculated? (Detailed Breakdown)</span>
          </div>
          {showTechnicalBreakdown ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
        </button>

        {showTechnicalBreakdown && (
          <div className="p-4 pt-0 border-t border-slate-200/60 dark:border-slate-800/60 space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 pt-4">
              <div className="p-3 bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800">
                <div className="flex justify-between text-xs mb-1.5">
                  <span className="font-medium">Required Skills (35%)</span>
                  <span className="font-bold text-blue-600">{breakdown.required_skills}%</span>
                </div>
                <Progress value={breakdown.required_skills} className="h-1.5" />
              </div>

              <div className="p-3 bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800">
                <div className="flex justify-between text-xs mb-1.5">
                  <span className="font-medium">Preferred Skills (15%)</span>
                  <span className="font-bold text-blue-600">{breakdown.preferred_skills}%</span>
                </div>
                <Progress value={breakdown.preferred_skills} className="h-1.5" />
              </div>

              <div className="p-3 bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800">
                <div className="flex justify-between text-xs mb-1.5">
                  <span className="font-medium">Experience Relevance (20%)</span>
                  <span className="font-bold text-blue-600">{breakdown.experience_relevance}%</span>
                </div>
                <Progress value={breakdown.experience_relevance} className="h-1.5" />
              </div>

              <div className="p-3 bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800">
                <div className="flex justify-between text-xs mb-1.5">
                  <span className="font-medium">Project Alignment (15%)</span>
                  <span className="font-bold text-blue-600">{breakdown.project_relevance}%</span>
                </div>
                <Progress value={breakdown.project_relevance} className="h-1.5" />
              </div>

              <div className="p-3 bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800">
                <div className="flex justify-between text-xs mb-1.5">
                  <span className="font-medium">Semantic Fit (15%)</span>
                  <span className="font-bold text-blue-600">{breakdown.semantic_alignment}%</span>
                </div>
                <Progress value={breakdown.semantic_alignment} className="h-1.5" />
              </div>
            </div>

            <div className="flex items-center gap-2 text-xs text-slate-500 pt-2">
              <ShieldCheck className="h-4 w-4 text-emerald-600 shrink-0" />
              <span>
                Truth Guard verified: All scores are mathematically calculated from your authentic profile evidence. No fabricated claims.
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Main Requirements List with Filter Tabs */}
      <div className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-200 dark:border-slate-800 pb-3">
          <div className="flex items-center gap-2">
            <h2 className="text-base font-semibold">Job Requirements Breakdown</h2>
            <Badge variant="outline" className="text-xs">
              {filteredItems.length} items
            </Badge>
          </div>

          <div className="flex items-center gap-1.5 bg-slate-100 dark:bg-slate-800/80 p-1 rounded-xl text-xs font-medium">
            <button
              onClick={() => setActiveTab("ALL")}
              className={`px-3 py-1 rounded-lg transition-colors ${
                activeTab === "ALL"
                  ? "bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 shadow-xs font-semibold"
                  : "text-slate-600 dark:text-slate-400 hover:text-slate-900"
              }`}
            >
              All ({match.items.length})
            </button>
            <button
              onClick={() => setActiveTab("MATCHED")}
              className={`px-3 py-1 rounded-lg transition-colors ${
                activeTab === "MATCHED"
                  ? "bg-white dark:bg-slate-900 text-emerald-700 dark:text-emerald-400 shadow-xs font-semibold"
                  : "text-slate-600 dark:text-slate-400 hover:text-emerald-700"
              }`}
            >
              Matched ({matchedCount})
            </button>
            <button
              onClick={() => setActiveTab("PARTIAL")}
              className={`px-3 py-1 rounded-lg transition-colors ${
                activeTab === "PARTIAL"
                  ? "bg-white dark:bg-slate-900 text-amber-700 dark:text-amber-400 shadow-xs font-semibold"
                  : "text-slate-600 dark:text-slate-400 hover:text-amber-700"
              }`}
            >
              Partial ({partialCount})
            </button>
            <button
              onClick={() => setActiveTab("MISSING")}
              className={`px-3 py-1 rounded-lg transition-colors ${
                activeTab === "MISSING"
                  ? "bg-white dark:bg-slate-900 text-rose-700 dark:text-rose-400 shadow-xs font-semibold"
                  : "text-slate-600 dark:text-slate-400 hover:text-rose-700"
              }`}
            >
              Missing ({missingCount})
            </button>
          </div>
        </div>

        {/* Requirements Cards */}
        {filteredItems.length === 0 ? (
          <div className="text-center py-12 rounded-xl border border-dashed border-slate-200 dark:border-slate-800 p-8 text-sm text-slate-500">
            No requirements match this filter.
          </div>
        ) : (
          <div className="space-y-3">
            {filteredItems.map((item) => {
              const reqDetails = getRequirementDetails(item.requirement_id);
              const isExpanded = !!expandedEvidenceIds[item.id];

              return (
                <div
                  key={item.id}
                  className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-4 shadow-2xs transition-all hover:border-slate-300 dark:hover:border-slate-700"
                >
                  <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
                    <div className="space-y-1.5 flex-1">
                      <div className="flex items-center gap-2">
                        {item.status === "MATCHED" && (
                          <span className="flex h-5 w-5 items-center justify-center rounded-full bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-400 text-xs font-bold">
                            ✓
                          </span>
                        )}
                        {item.status === "PARTIAL" && (
                          <span className="flex h-5 w-5 items-center justify-center rounded-full bg-amber-100 text-amber-700 dark:bg-amber-950 dark:text-amber-400 text-xs font-bold">
                            !
                          </span>
                        )}
                        {item.status === "MISSING" && (
                          <span className="flex h-5 w-5 items-center justify-center rounded-full bg-rose-100 text-rose-700 dark:bg-rose-950 dark:text-rose-400 text-xs font-bold">
                            ✕
                          </span>
                        )}
                        <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100">
                          {getRequirementText(item.requirement_id)}
                        </h3>
                      </div>

                      <div className="flex flex-wrap items-center gap-2 text-xs text-slate-500 pl-7">
                        {reqDetails && (
                          <>
                            <span className="rounded bg-slate-100 dark:bg-slate-800 px-2 py-0.5 font-medium">
                              {reqDetails.category}
                            </span>
                            <span
                              className={`rounded px-2 py-0.5 font-medium ${
                                reqDetails.importance === "REQUIRED"
                                  ? "bg-rose-50 text-rose-700 dark:bg-rose-950/60 dark:text-rose-400"
                                  : "bg-blue-50 text-blue-700 dark:bg-blue-950/60 dark:text-blue-400"
                              }`}
                            >
                              {reqDetails.importance}
                            </span>
                          </>
                        )}
                        <span className="text-slate-400">•</span>
                        <span>{item.explanation || "Analyzed against your profile."}</span>
                      </div>
                    </div>

                    {/* Toggle Evidence Accordion */}
                    <button
                      onClick={() => toggleEvidence(item.id)}
                      className="self-start sm:self-center shrink-0 text-xs font-medium text-blue-600 hover:text-blue-700 dark:text-blue-400 flex items-center gap-1 pl-7 sm:pl-0"
                    >
                      <span>{isExpanded ? "Hide evidence" : "View evidence"}</span>
                      {isExpanded ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
                    </button>
                  </div>

                  {/* Collapsible Progressive Disclosure Evidence */}
                  {isExpanded && (
                    <div className="mt-3 ml-7 pt-3 border-t border-slate-100 dark:border-slate-800 text-xs space-y-2">
                      <div className="flex items-center justify-between text-slate-500">
                        <span className="font-semibold uppercase tracking-wider text-[10px]">
                          Profile Attribution
                        </span>
                        <span>Confidence: {Math.round(item.score * 100)}%</span>
                      </div>

                      {item.matched_entity_name ? (
                        <p className="text-slate-700 dark:text-slate-300">
                          Matched evidence from: <strong>{item.matched_entity_name}</strong> ({item.matched_entity_type})
                        </p>
                      ) : (
                        <p className="text-slate-500 italic">
                          No direct profile evidence found. Consider adding this skill to your Master Career Profile.
                        </p>
                      )}

                      {item.evidence_summary && (
                        <blockquote className="rounded-lg bg-slate-50 dark:bg-slate-800/60 p-2.5 text-slate-600 dark:text-slate-300 italic border-l-2 border-blue-500">
                          &ldquo;{item.evidence_summary}&rdquo;
                        </blockquote>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
