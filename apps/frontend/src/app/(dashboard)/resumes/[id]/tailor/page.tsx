"use client";

import * as React from "react";
import Link from "next/link";
import { useParams, useSearchParams, useRouter } from "next/navigation";
import {
  ArrowLeft,
  Check,
  X,
  AlertTriangle,
  ShieldCheck,
  ShieldAlert,
  Sparkles,
  GitCommit,
  GitBranch,
  RefreshCw,
  Edit2,
  FileText,
  TrendingUp,
  Layers,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { LoadingState } from "@/components/shared/loading-state";
import { ErrorState } from "@/components/shared/error-state";
import { useResumeDetail } from "@/lib/hooks/use-resumes";
import { useJobs } from "@/lib/hooks/use-jobs";
import {
  useTailorMutation,
  useUpdateSuggestionMutation,
  useApplySuggestionsMutation,
  useVersionTailoringJobs,
} from "@/lib/hooks/use-tailoring";
import type {
  ResumeSuggestion,
  TailoringApplyResponse,
  TruthGuardStatus,
} from "@/types/tailoring";

export default function ResumeTailoringPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const router = useRouter();

  const resumeId = (params?.id as string) || "";
  const initialVersionId = searchParams.get("versionId") || "";
  const initialJobId = searchParams.get("jobId") || "";

  // 1. Data queries
  const { resume, versions, isLoading: isResumeLoading } = useResumeDetail(resumeId);
  const { jobs, isLoading: isJobsLoading } = useJobs();

  // Selected version and target job state
  const [selectedVersionId, setSelectedVersionId] = React.useState<string>(initialVersionId);
  const [selectedJobId, setSelectedJobId] = React.useState<string>(initialJobId);

  // Set default selected version if none specified
  React.useEffect(() => {
    if (!selectedVersionId && versions.length > 0) {
      const active = versions.find((v) => v.id === resume?.active_version_id);
      setSelectedVersionId(active ? active.id : versions[0].id);
    }
  }, [versions, resume, selectedVersionId]);

  // Set default target job if none specified
  React.useEffect(() => {
    if (!selectedJobId && jobs.length > 0) {
      setSelectedJobId(jobs[0].id);
    }
  }, [jobs, selectedJobId]);

  // 2. Tailoring jobs for this version
  const {
    data: tailoringJobs = [],
    isLoading: isTailoringJobsLoading,
    refetch: refetchJobs,
  } = useVersionTailoringJobs(selectedVersionId);

  const activeJob = tailoringJobs.length > 0 ? tailoringJobs[0] : null;

  // 3. Mutations
  const tailorMutation = useTailorMutation(selectedVersionId);
  const updateSuggestionMutation = useUpdateSuggestionMutation(activeJob?.id);
  const applySuggestionsMutation = useApplySuggestionsMutation(resumeId, selectedVersionId);

  // Section filter state
  const [selectedSection, setSelectedSection] = React.useState<string>("ALL");
  const [expandedBreakdownId, setExpandedBreakdownId] = React.useState<string | null>(null);

  // Edit suggestion modal state
  const [editingSuggestion, setEditingSuggestion] = React.useState<ResumeSuggestion | null>(null);
  const [editedContent, setEditedContent] = React.useState<string>("");
  const [editNotes, setEditNotes] = React.useState<string>("");

  // Post-apply result modal state
  const [applyResult, setApplyResult] = React.useState<TailoringApplyResponse | null>(null);
  const [applyModalOpen, setApplyModalOpen] = React.useState<boolean>(false);

  // Trigger tailoring handler
  const handleTriggerTailoring = async () => {
    if (!selectedJobId || !selectedVersionId) return;
    try {
      await tailorMutation.mutateAsync({ job_description_id: selectedJobId });
      refetchJobs();
    } catch (err) {
      console.error("Failed to run tailoring", err);
    }
  };

  // Suggestion action handlers
  const handleAccept = async (sug: ResumeSuggestion) => {
    await updateSuggestionMutation.mutateAsync({
      suggestionId: sug.id,
      payload: { status: "ACCEPTED" },
    });
  };

  const handleReject = async (sug: ResumeSuggestion) => {
    await updateSuggestionMutation.mutateAsync({
      suggestionId: sug.id,
      payload: { status: "REJECTED" },
    });
  };

  const handleOpenEdit = (sug: ResumeSuggestion) => {
    setEditingSuggestion(sug);
    setEditedContent(sug.proposed_content);
    setEditNotes(sug.user_notes || "");
  };

  const handleSaveEdit = async () => {
    if (!editingSuggestion) return;
    await updateSuggestionMutation.mutateAsync({
      suggestionId: editingSuggestion.id,
      payload: {
        status: "MODIFIED",
        proposed_content: editedContent,
        user_notes: editNotes,
      },
    });
    setEditingSuggestion(null);
  };

  // Apply accepted suggestions handler
  const acceptedSuggestions =
    activeJob?.suggestions.filter((s) => s.status === "ACCEPTED" || s.status === "MODIFIED") || [];

  const handleApply = async () => {
    if (acceptedSuggestions.length === 0 || !selectedVersionId) return;
    try {
      const res = await applySuggestionsMutation.mutateAsync({
        suggestion_ids: acceptedSuggestions.map((s) => s.id),
        change_summary: `Tailored version with ${acceptedSuggestions.length} accepted improvements`,
        trigger_match: true,
      });
      setApplyResult(res);
      setApplyModalOpen(true);
    } catch (err) {
      console.error("Failed to apply suggestions", err);
    }
  };

  if (isResumeLoading || isJobsLoading) {
    return <LoadingState message="Loading Tailoring & Truth Guard Workspace..." />;
  }

  if (!resume) {
    return (
      <ErrorState
        title="Resume not found"
        message="The specified resume family could not be loaded."
      />
    );
  }

  const selectedJob = jobs.find((j) => j.id === selectedJobId);
  const selectedVersion = versions.find((v) => v.id === selectedVersionId);

  // Suggestions filtered by section
  const suggestions = activeJob?.suggestions || [];
  const filteredSuggestions =
    selectedSection === "ALL"
      ? suggestions
      : suggestions.filter((s) => s.section.toUpperCase() === selectedSection.toUpperCase());

  // Statistics
  const verifiedCount = suggestions.filter((s) => s.truth_guard_status === "VERIFIED").length;
  const reviewCount = suggestions.filter((s) => s.truth_guard_status === "REQUIRES_REVIEW" || s.truth_guard_status === "PARTIALLY_SUPPORTED").length;
  const unsupportedCount = suggestions.filter((s) => s.truth_guard_status === "UNSUPPORTED").length;

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-16">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b pb-4">
        <div>
          <Link
            href={`/resumes/${resumeId}`}
            className="text-xs text-muted-foreground hover:text-foreground inline-flex items-center gap-1 mb-2"
          >
            <ArrowLeft className="h-3 w-3" /> Back to {resume.title}
          </Link>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight">AI Tailoring & Truth Guard</h1>
            <Badge variant="outline" className="border-primary/40 text-primary gap-1 text-xs">
              <Sparkles className="h-3 w-3" /> Grounded Engine
            </Badge>
          </div>
          <p className="text-xs text-muted-foreground mt-0.5">
            Evaluate section-by-section improvements against verified Master Career Profile facts.
          </p>
        </div>

        {/* Action Controls: Version & Target Job Selector */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-1.5 text-xs bg-muted/40 p-1.5 rounded-lg border">
            <span className="text-muted-foreground font-medium pl-1">Version:</span>
            <select
              value={selectedVersionId}
              onChange={(e) => setSelectedVersionId(e.target.value)}
              className="bg-background border rounded px-2 py-1 text-xs font-mono"
            >
              {versions.map((v) => (
                <option key={v.id} value={v.id}>
                  {v.version_number} {v.id === resume.active_version_id ? "(Active)" : ""}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-1.5 text-xs bg-muted/40 p-1.5 rounded-lg border">
            <span className="text-muted-foreground font-medium pl-1">Target Job:</span>
            <select
              value={selectedJobId}
              onChange={(e) => setSelectedJobId(e.target.value)}
              className="bg-background border rounded px-2 py-1 text-xs max-w-[200px] truncate"
            >
              {jobs.map((j) => (
                <option key={j.id} value={j.id}>
                  {j.title} {j.company ? `(${j.company})` : ""}
                </option>
              ))}
            </select>
          </div>

          <Button
            onClick={handleTriggerTailoring}
            disabled={tailorMutation.isPending || !selectedJobId}
            className="gap-1.5 text-xs"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${tailorMutation.isPending ? "animate-spin" : ""}`} />
            {tailorMutation.isPending ? "Auditing Evidence..." : "Run Tailoring"}
          </Button>
        </div>
      </div>

      {/* Target Job Info Card */}
      {selectedJob && (
        <Card className="bg-primary/[0.02] border-primary/20">
          <CardContent className="p-4 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="text-xs font-semibold uppercase text-primary tracking-wider">Target Role:</span>
                <span className="text-sm font-semibold">{selectedJob.title}</span>
                {selectedJob.company && (
                  <Badge variant="outline" className="text-xs">
                    {selectedJob.company}
                  </Badge>
                )}
              </div>
              <p className="text-xs text-muted-foreground line-clamp-1">
                {selectedJob.raw_text.substring(0, 160)}...
              </p>
            </div>

            {/* Truth Guard Safety Stats */}
            {suggestions.length > 0 && (
              <div className="flex items-center gap-2 shrink-0">
                <div className="flex items-center gap-1 text-xs px-2.5 py-1 rounded bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border border-emerald-500/30">
                  <ShieldCheck className="h-3.5 w-3.5" />
                  <span className="font-semibold">{verifiedCount}</span> Verified
                </div>
                {reviewCount > 0 && (
                  <div className="flex items-center gap-1 text-xs px-2.5 py-1 rounded bg-amber-500/10 text-amber-700 dark:text-amber-400 border border-amber-500/30">
                    <AlertTriangle className="h-3.5 w-3.5" />
                    <span className="font-semibold">{reviewCount}</span> Review Needed
                  </div>
                )}
                {unsupportedCount > 0 && (
                  <div className="flex items-center gap-1 text-xs px-2.5 py-1 rounded bg-rose-500/10 text-rose-700 dark:text-rose-400 border border-rose-500/30">
                    <ShieldAlert className="h-3.5 w-3.5" />
                    <span className="font-semibold">{unsupportedCount}</span> Hallucinations Blocked
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Main Suggestions Workspace */}
      {isTailoringJobsLoading ? (
        <LoadingState message="Loading generated suggestions..." />
      ) : suggestions.length === 0 ? (
        <Card className="p-12 text-center border-dashed">
          <div className="max-w-md mx-auto space-y-3">
            <Sparkles className="h-10 w-10 text-primary mx-auto opacity-70" />
            <h3 className="text-base font-semibold">No Tailoring Suggestions Generated Yet</h3>
            <p className="text-xs text-muted-foreground leading-relaxed">
              Select your target job description above and click <strong>&quot;Run Tailoring&quot;</strong>.
              ResumeForge will extract required skills, analyze your Master Career Profile, and generate
              grounded, non-hallucinated section improvements.
            </p>
            <Button
              onClick={handleTriggerTailoring}
              disabled={tailorMutation.isPending || !selectedJobId}
              className="gap-1.5 text-xs mt-2"
            >
              <Sparkles className="h-3.5 w-3.5" /> Start Tailoring Run
            </Button>
          </div>
        </Card>
      ) : (
        <div className="space-y-4">
          {/* Section Filter Pills & Selection Counter */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-muted/20 p-2 rounded-lg border">
            <div className="flex items-center gap-1 overflow-x-auto text-xs">
              {["ALL", "SUMMARY", "SKILLS", "EXPERIENCE", "PROJECTS"].map((sec) => (
                <button
                  key={sec}
                  onClick={() => setSelectedSection(sec)}
                  className={`px-3 py-1.5 rounded-md font-medium transition-all ${
                    selectedSection === sec
                      ? "bg-primary text-primary-foreground shadow-sm"
                      : "text-muted-foreground hover:bg-muted/80"
                  }`}
                >
                  {sec}
                  <span className="ml-1.5 opacity-70 text-[10px]">
                    ({sec === "ALL" ? suggestions.length : suggestions.filter((s) => s.section.toUpperCase() === sec).length})
                  </span>
                </button>
              ))}
            </div>

            {/* Apply Action Bar */}
            <div className="flex items-center gap-3 shrink-0">
              <span className="text-xs text-muted-foreground">
                <strong className="text-foreground">{acceptedSuggestions.length}</strong> accepted
              </span>
              <Button
                onClick={handleApply}
                disabled={acceptedSuggestions.length === 0 || applySuggestionsMutation.isPending}
                size="sm"
                className="gap-1.5 text-xs bg-emerald-600 hover:bg-emerald-700 text-white"
              >
                <GitBranch className="h-3.5 w-3.5" />
                {applySuggestionsMutation.isPending ? "Creating Version..." : `Apply & Create Version (${acceptedSuggestions.length})`}
              </Button>
            </div>
          </div>

          {/* Suggestion Cards List */}
          <div className="space-y-4">
            {filteredSuggestions.map((sug) => {
              const isAccepted = sug.status === "ACCEPTED" || sug.status === "MODIFIED";
              const isRejected = sug.status === "REJECTED";
              const isUnsupported = sug.truth_guard_status === "UNSUPPORTED";
              const isExpanded = expandedBreakdownId === sug.id;

              return (
                <Card
                  key={sug.id}
                  className={`transition-all border ${
                    isAccepted
                      ? "border-emerald-500/50 bg-emerald-500/[0.02]"
                      : isRejected
                      ? "opacity-60 border-muted"
                      : isUnsupported
                      ? "border-rose-500/40 bg-rose-500/[0.02]"
                      : "hover:border-primary/40"
                  }`}
                >
                  <CardHeader className="p-4 pb-2">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <Badge variant="outline" className="font-mono text-xs uppercase tracking-wider">
                          {sug.section}
                        </Badge>
                        <Badge
                          variant="secondary"
                          className="text-[11px] font-medium bg-muted"
                        >
                          {sug.suggestion_type.replace(/_/g, " ")}
                        </Badge>

                        {/* Truth Guard Badge */}
                        <TruthGuardBadge status={sug.truth_guard_status} />
                      </div>

                      {/* Action buttons */}
                      <div className="flex items-center gap-1.5">
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => handleOpenEdit(sug)}
                          className="h-7 px-2 text-xs gap-1"
                        >
                          <Edit2 className="h-3 w-3" /> Edit
                        </Button>
                        <Button
                          size="sm"
                          variant={isAccepted ? "default" : "outline"}
                          onClick={() => handleAccept(sug)}
                          disabled={isUnsupported}
                          className={`h-7 px-2.5 text-xs gap-1 ${
                            isAccepted ? "bg-emerald-600 hover:bg-emerald-700 text-white" : ""
                          }`}
                        >
                          <Check className="h-3 w-3" /> {isAccepted ? "Accepted" : "Accept"}
                        </Button>
                        <Button
                          size="sm"
                          variant={isRejected ? "secondary" : "ghost"}
                          onClick={() => handleReject(sug)}
                          className="h-7 px-2 text-xs text-muted-foreground hover:text-destructive"
                        >
                          <X className="h-3 w-3" /> Reject
                        </Button>
                      </div>
                    </div>
                  </CardHeader>

                  <CardContent className="p-4 pt-2 space-y-3">
                    {/* Content Comparison */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                      {/* Original Content if available */}
                      {sug.original_content ? (
                        <div className="p-2.5 rounded bg-muted/30 border border-muted font-mono leading-relaxed">
                          <span className="text-[10px] uppercase font-bold text-muted-foreground block mb-1">
                            Original
                          </span>
                          <p className="text-muted-foreground line-through opacity-80">{sug.original_content}</p>
                        </div>
                      ) : (
                        <div className="p-2.5 rounded bg-muted/20 border border-dashed border-muted text-muted-foreground flex items-center justify-center">
                          <span className="text-[11px] italic">Addition from Master Profile (not in original version)</span>
                        </div>
                      )}

                      {/* Proposed Tailored Content */}
                      <div
                        className={`p-2.5 rounded border font-mono leading-relaxed ${
                          isUnsupported
                            ? "bg-rose-500/10 border-rose-500/30 text-rose-950 dark:text-rose-200"
                            : "bg-emerald-500/10 border-emerald-500/30 text-emerald-950 dark:text-emerald-200"
                        }`}
                      >
                        <span className="text-[10px] uppercase font-bold text-emerald-700 dark:text-emerald-400 block mb-1">
                          Tailored Suggestion
                        </span>
                        <p className="font-sans font-medium">{sug.proposed_content}</p>
                      </div>
                    </div>

                    {/* Grounding Explanation */}
                    <div className="text-xs text-muted-foreground flex items-start gap-1.5 pt-1">
                      <Sparkles className="h-3.5 w-3.5 text-primary shrink-0 mt-0.5" />
                      <span>{sug.reason}</span>
                    </div>

                    {/* Unsupported Warning Banner */}
                    {isUnsupported && (
                      <div className="p-2.5 rounded-lg bg-rose-500/10 border border-rose-500/30 text-xs text-rose-700 dark:text-rose-400 flex items-start gap-2">
                        <ShieldAlert className="h-4 w-4 shrink-0 mt-0.5" />
                        <div>
                          <strong>Truth Guard Blocked Claim:</strong> {sug.truth_guard_reason}
                          <p className="text-[11px] mt-0.5 opacity-90">
                            ResumeForge prohibits inventing metrics or technologies. Edit the claim to match your verified career facts before accepting.
                          </p>
                        </div>
                      </div>
                    )}

                    {/* Evidence Badges */}
                    {sug.evidence_items && sug.evidence_items.length > 0 && (
                      <div className="flex flex-wrap items-center gap-1.5 pt-1">
                        <span className="text-[11px] font-semibold text-muted-foreground">Evidence:</span>
                        {sug.evidence_items.map((ev, idx) => (
                          <Badge
                            key={idx}
                            variant="outline"
                            className="text-[10px] gap-1 bg-background border-emerald-500/30 text-emerald-700 dark:text-emerald-400"
                          >
                            <ShieldCheck className="h-3 w-3" />
                            {ev.evidence_type}: {ev.supporting_text || "Master Profile Record"}
                          </Badge>
                        ))}
                      </div>
                    )}

                    {/* Claim Breakdown Accordion Toggle */}
                    {sug.claim_breakdown_json && sug.claim_breakdown_json.length > 0 && (
                      <div className="pt-1">
                        <button
                          onClick={() => setExpandedBreakdownId(isExpanded ? null : sug.id)}
                          className="text-[11px] text-muted-foreground hover:text-foreground inline-flex items-center gap-1"
                        >
                          {isExpanded ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
                          {isExpanded ? "Hide Claim-Level Audit" : `View Claim-Level Audit (${sug.claim_breakdown_json.length} clauses)`}
                        </button>

                        {isExpanded && (
                          <div className="mt-2 space-y-1.5 p-3 rounded-md bg-muted/30 border text-xs">
                            <span className="font-semibold text-foreground text-[11px] block mb-1">
                              Truth Guard Clause Inspection:
                            </span>
                            {sug.claim_breakdown_json.map((c, cIdx) => (
                              <div
                                key={cIdx}
                                className="p-2 rounded bg-background border flex items-start justify-between gap-2"
                              >
                                <div className="space-y-0.5">
                                  <p className="font-mono text-[11px]">{c.claim_text}</p>
                                  {c.reasons && c.reasons.length > 0 && (
                                    <p className="text-[10px] text-muted-foreground">{c.reasons.join("; ")}</p>
                                  )}
                                </div>
                                <TruthGuardBadge status={c.status} />
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </div>
      )}

      {/* Edit Suggestion Modal */}
      <Dialog open={!!editingSuggestion} onOpenChange={(open) => !open && setEditingSuggestion(null)}>
        <DialogContent className="max-w-xl">
          <DialogHeader>
            <DialogTitle>Edit Tailored Suggestion</DialogTitle>
            <DialogDescription>
              Fine-tune the proposed content. Truth Guard will audit your modifications to prevent accidental hallucinations.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-3 py-2">
            <div>
              <label className="text-xs font-semibold uppercase text-muted-foreground mb-1 block">
                Proposed Content
              </label>
              <Textarea
                rows={4}
                value={editedContent}
                onChange={(e) => setEditedContent(e.target.value)}
                className="font-mono text-xs"
              />
            </div>

            <div>
              <label className="text-xs font-semibold uppercase text-muted-foreground mb-1 block">
                User Notes (Optional)
              </label>
              <Input
                placeholder="Why was this modified?"
                value={editNotes}
                onChange={(e) => setEditNotes(e.target.value)}
                className="text-xs"
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setEditingSuggestion(null)}>
              Cancel
            </Button>
            <Button onClick={handleSaveEdit}>
              Save & Verify with Truth Guard
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Post-Apply Result & Diff Modal */}
      <Dialog open={applyModalOpen} onOpenChange={setApplyModalOpen}>
        <DialogContent className="max-w-4xl max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-emerald-600" />
              Tailored Version Created ({applyResult?.version_number})
            </DialogTitle>
            <DialogDescription>
              Your accepted suggestions have been applied into an immutable snapshot.
            </DialogDescription>
          </DialogHeader>

          {applyResult && (
            <div className="space-y-6 py-2">
              {/* Before vs After Match Score Comparison Card */}
              {applyResult.after_match && (
                <Card className="bg-primary/[0.03] border-primary/20">
                  <CardHeader className="p-4 pb-2">
                    <CardTitle className="text-sm font-semibold flex items-center gap-1.5">
                      <TrendingUp className="h-4 w-4 text-primary" /> Before vs After Match Performance
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="p-4 pt-1 space-y-4">
                    <div className="flex items-center justify-around text-center py-2 bg-background border rounded-lg">
                      <div>
                        <span className="text-xs text-muted-foreground block">Before Match Score</span>
                        <span className="text-2xl font-bold font-mono text-muted-foreground">
                          {applyResult.before_match?.overall_score ?? "--"}/100
                        </span>
                      </div>
                      <div className="flex flex-col items-center">
                        <span className="text-xs font-semibold text-emerald-600 block mb-0.5">
                          {applyResult.score_delta !== null && applyResult.score_delta !== undefined
                            ? applyResult.score_delta >= 0
                              ? `+${applyResult.score_delta} Score Increase`
                              : `${applyResult.score_delta} Score Decrease`
                            : "New Match"}
                        </span>
                        <ArrowLeft className="h-5 w-5 text-emerald-600 rotate-180" />
                      </div>
                      <div>
                        <span className="text-xs text-emerald-600 font-semibold block">Tailored Match Score</span>
                        <span className="text-2xl font-bold font-mono text-emerald-600">
                          {applyResult.after_match.overall_score}/100
                        </span>
                      </div>
                    </div>

                    {/* Breakdown comparison */}
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
                      <div className="p-2 rounded bg-muted/40">
                        <span className="text-[10px] text-muted-foreground block">Required Skills</span>
                        <span className="font-semibold font-mono">{applyResult.after_match.required_skills_score}%</span>
                      </div>
                      <div className="p-2 rounded bg-muted/40">
                        <span className="text-[10px] text-muted-foreground block">Preferred Skills</span>
                        <span className="font-semibold font-mono">{applyResult.after_match.preferred_skills_score}%</span>
                      </div>
                      <div className="p-2 rounded bg-muted/40">
                        <span className="text-[10px] text-muted-foreground block">Experience Score</span>
                        <span className="font-semibold font-mono">{applyResult.after_match.experience_score}%</span>
                      </div>
                      <div className="p-2 rounded bg-muted/40">
                        <span className="text-[10px] text-muted-foreground block">Semantic Score</span>
                        <span className="font-semibold font-mono">{applyResult.after_match.semantic_score}%</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Line-by-Line Diff Viewer */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold uppercase text-muted-foreground flex items-center gap-1.5">
                    <FileText className="h-3.5 w-3.5" /> Transparent Line-by-Line Diff
                  </span>
                  <div className="flex items-center gap-2 text-xs">
                    <span className="text-emerald-600 font-mono font-semibold">+{applyResult.diff.added_lines}</span>
                    <span className="text-rose-600 font-mono font-semibold">-{applyResult.diff.removed_lines}</span>
                    <Badge variant="outline" className="text-[10px] font-mono">
                      {applyResult.diff.similarity_ratio}% similarity
                    </Badge>
                  </div>
                </div>

                <div className="border rounded-lg bg-muted/20 p-3 font-mono text-xs max-h-72 overflow-y-auto space-y-0.5">
                  {applyResult.diff.line_diffs.map((line, idx) => {
                    const isAdd = line.type === "ADD";
                    const isRemove = line.type === "REMOVE";
                    return (
                      <div
                        key={idx}
                        className={`px-2 py-0.5 rounded leading-relaxed whitespace-pre-wrap ${
                          isAdd
                            ? "bg-emerald-500/15 text-emerald-800 dark:text-emerald-300 font-medium"
                            : isRemove
                            ? "bg-rose-500/15 text-rose-800 dark:text-rose-300 line-through opacity-75"
                            : "text-muted-foreground"
                        }`}
                      >
                        <span className="select-none inline-block w-4 opacity-50">
                          {isAdd ? "+" : isRemove ? "-" : " "}
                        </span>
                        {line.content}
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          )}

          <DialogFooter className="flex items-center justify-between sm:justify-between w-full">
            <Button
              variant="outline"
              onClick={() => {
                setApplyModalOpen(false);
                router.push(`/resumes/${resumeId}`);
              }}
            >
              View in Resume History
            </Button>
            <Button
              onClick={() => setApplyModalOpen(false)}
              className="bg-emerald-600 hover:bg-emerald-700 text-white"
            >
              Done
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

function TruthGuardBadge({ status }: { status: TruthGuardStatus }) {
  if (status === "VERIFIED") {
    return (
      <Badge
        variant="outline"
        className="text-[10px] font-semibold bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border-emerald-500/30 gap-1"
      >
        <ShieldCheck className="h-3 w-3" /> Verified
      </Badge>
    );
  }
  if (status === "PARTIALLY_SUPPORTED") {
    return (
      <Badge
        variant="outline"
        className="text-[10px] font-semibold bg-amber-500/10 text-amber-700 dark:text-amber-400 border-amber-500/30 gap-1"
      >
        <AlertTriangle className="h-3 w-3" /> Partially Supported
      </Badge>
    );
  }
  if (status === "REQUIRES_REVIEW") {
    return (
      <Badge
        variant="outline"
        className="text-[10px] font-semibold bg-purple-500/10 text-purple-700 dark:text-purple-400 border-purple-500/30 gap-1"
      >
        <AlertTriangle className="h-3 w-3" /> Requires Review
      </Badge>
    );
  }
  return (
    <Badge
      variant="outline"
      className="text-[10px] font-semibold bg-rose-500/10 text-rose-700 dark:text-rose-400 border-rose-500/30 gap-1"
    >
      <ShieldAlert className="h-3 w-3" /> Unsupported
    </Badge>
  );
}
