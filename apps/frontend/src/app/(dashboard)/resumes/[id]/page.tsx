"use client";

import * as React from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  ArrowLeft,
  Check,
  Copy,
  FileText,
  FileUp,
  GitBranch,
  GitCommit,
  Plus,
  AlertCircle,
  FileCode,
  Sparkles,
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
import { formatRelativeTime } from "@/lib/utils";
import type { ResumeVersion } from "@/types/resume";

export default function ResumeDetailPage() {
  const params = useParams();
  const resumeId = (params?.id as string) || "";

  const {
    resume,
    isLoading,
    isError,
    versions,
    isVersionsLoading,
    createVersion,
    uploadVersion,
    isUploading,
    cloneVersion,
    isCloning,
    activateVersion,
    isActivating,
  } = useResumeDetail(resumeId);

  // Selected version for inspection
  const [selectedVersionId, setSelectedVersionId] = React.useState<string | null>(null);

  // Modals state
  const [uploadModalOpen, setUploadModalOpen] = React.useState(false);
  const [cloneModalOpen, setCloneModalOpen] = React.useState(false);
  const [targetCloneVersion, setTargetCloneVersion] = React.useState<ResumeVersion | null>(null);

  // Upload form state
  const [uploadFile, setUploadFile] = React.useState<File | null>(null);
  const [uploadVersionNumber, setUploadVersionNumber] = React.useState("");
  const [uploadSummary, setUploadSummary] = React.useState("");
  const [uploadError, setUploadError] = React.useState<string | null>(null);

  // Clone form state
  const [cloneVersionNumber, setCloneVersionNumber] = React.useState("");
  const [cloneSummary, setCloneSummary] = React.useState("");

  // Default selected version to active version on initial load
  React.useEffect(() => {
    if (resume?.active_version_id && !selectedVersionId) {
      setSelectedVersionId(resume.active_version_id);
    } else if (versions.length > 0 && !selectedVersionId) {
      setSelectedVersionId(versions[0].id);
    }
  }, [resume, versions, selectedVersionId]);

  if (isLoading || isVersionsLoading) {
    return <LoadingState message="Loading resume versions..." />;
  }

  if (isError || !resume) {
    return (
      <ErrorState
        title="Resume not found"
        message="The requested resume family could not be found or does not belong to you."
      />
    );
  }

  const selectedVersion =
    versions.find((v) => v.id === selectedVersionId) ||
    versions.find((v) => v.id === resume.active_version_id) ||
    versions[0];

  const handleOpenUpload = () => {
    // Propose next version number
    const nextMinor = versions.length + 1;
    setUploadVersionNumber(`v1.${nextMinor}`);
    setUploadSummary("");
    setUploadFile(null);
    setUploadError(null);
    setUploadModalOpen(true);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setUploadError(null);
    const file = e.target.files?.[0];
    if (!file) return;

    const lower = file.name.toLowerCase();
    if (!lower.endsWith(".pdf") && !lower.endsWith(".docx")) {
      setUploadError("Only .pdf and .docx files are permitted.");
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      setUploadError("File exceeds 10MB maximum limit.");
      return;
    }

    setUploadFile(file);
    if (!uploadSummary) {
      setUploadSummary(`Uploaded ${file.name}`);
    }
  };

  const handleUploadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadFile) {
      setUploadError("Please select a valid PDF or DOCX file.");
      return;
    }

    try {
      const created = await uploadVersion({
        file: uploadFile,
        versionNumber: uploadVersionNumber || undefined,
        changeSummary: uploadSummary || undefined,
      });
      setUploadModalOpen(false);
      setSelectedVersionId(created.id);
    } catch (err: unknown) {
      setUploadError(err instanceof Error ? err.message : "Upload processing failed");
    }
  };

  const handleOpenClone = (version: ResumeVersion) => {
    setTargetCloneVersion(version);
    setCloneVersionNumber(`${version.version_number}.1`);
    setCloneSummary(`Cloned from ${version.version_number}`);
    setCloneModalOpen(true);
  };

  const handleCloneSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!targetCloneVersion || !cloneVersionNumber.trim()) return;

    const cloned = await cloneVersion({
      versionId: targetCloneVersion.id,
      payload: {
        version_number: cloneVersionNumber,
        change_summary: cloneSummary,
      },
    });

    setCloneModalOpen(false);
    setSelectedVersionId(cloned.id);
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Top Navigation */}
      <div>
        <Button variant="ghost" size="sm" asChild className="mb-2 -ml-2 text-xs">
          <Link href="/resumes">
            <ArrowLeft className="h-3.5 w-3.5 mr-1" /> Back to Resumes
          </Link>
        </Button>

        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl font-bold tracking-tight">{resume.title}</h1>
              <Badge variant="outline" className="font-mono text-xs">
                {versions.length} {versions.length === 1 ? "version" : "versions"}
              </Badge>
            </div>
            {resume.target_role && (
              <p className="text-sm font-medium text-primary mt-1">
                Target: {resume.target_role} {resume.target_company && `• ${resume.target_company}`}
              </p>
            )}
            {resume.description && (
              <p className="text-xs text-muted-foreground mt-0.5">{resume.description}</p>
            )}
          </div>

          <div className="flex items-center gap-2 shrink-0">
            <Link href={`/resumes/${resume.id}/tailor?versionId=${selectedVersion?.id || ""}`}>
              <Button variant="outline" className="gap-1.5 text-xs border-primary/40 text-primary hover:bg-primary/10">
                <Sparkles className="h-4 w-4" /> AI Tailor for Job
              </Button>
            </Link>
            <Button onClick={handleOpenUpload} className="gap-1.5 text-xs">
              <FileUp className="h-4 w-4" /> Upload New Version
            </Button>
          </div>
        </div>
      </div>

      {/* Main Grid: Left Timeline / Right Inspector */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Version History Timeline (5 cols) */}
        <div className="lg:col-span-5 space-y-3">
          <div className="flex items-center justify-between pb-1">
            <h2 className="text-sm font-semibold flex items-center gap-1.5">
              <GitBranch className="h-4 w-4" /> Version History
            </h2>
            <span className="text-xs text-muted-foreground">Immutable snapshots</span>
          </div>

          <div className="space-y-2">
            {versions.map((version) => {
              const isActive = resume.active_version_id === version.id;
              const isSelected = selectedVersion?.id === version.id;

              return (
                <div
                  key={version.id}
                  onClick={() => setSelectedVersionId(version.id)}
                  className={`p-3.5 rounded-lg border text-sm cursor-pointer transition-all ${
                    isSelected
                      ? "border-primary bg-primary/5 shadow-sm"
                      : "border-border hover:bg-muted/40"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <GitCommit className="h-4 w-4 text-muted-foreground" />
                      <span className="font-mono font-semibold text-sm">
                        {version.version_number}
                      </span>
                      {isActive && (
                        <Badge className="bg-primary/90 text-[10px] py-0 px-1.5 gap-1">
                          <Check className="h-3 w-3" /> Active
                        </Badge>
                      )}
                    </div>
                    <Badge
                      variant={version.status === "READY" ? "outline" : "secondary"}
                      className="text-[10px]"
                    >
                      {version.status}
                    </Badge>
                  </div>

                  <p className="text-xs text-muted-foreground mt-1.5 line-clamp-1">
                    {version.change_summary || "No change summary specified."}
                  </p>

                  <div className="flex items-center justify-between text-[11px] text-muted-foreground mt-3 pt-2 border-t border-border/50">
                    <span>{formatRelativeTime(version.created_at)}</span>
                    <div className="flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
                      {!isActive && version.status === "READY" && (
                        <button
                          type="button"
                          disabled={isActivating}
                          onClick={() => activateVersion(version.id)}
                          className="text-primary hover:underline font-medium"
                        >
                          Set Active
                        </button>
                      )}
                      <button
                        type="button"
                        disabled={isCloning}
                        onClick={() => handleOpenClone(version)}
                        className="text-muted-foreground hover:text-foreground flex items-center gap-0.5"
                      >
                        <Copy className="h-3 w-3" /> Clone
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right Column: Version Inspector & Text Preview (7 cols) */}
        <div className="lg:col-span-7">
          {selectedVersion ? (
            <Card className="h-full flex flex-col">
              <CardHeader className="p-5 pb-3 border-b">
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-base font-semibold flex items-center gap-2">
                      <FileCode className="h-4 w-4 text-primary" />
                      Version {selectedVersion.version_number} Snapshot
                    </CardTitle>
                    <CardDescription className="text-xs mt-0.5">
                      Created {formatRelativeTime(selectedVersion.created_at)}
                    </CardDescription>
                  </div>
                  <div className="flex items-center gap-2">
                    <Link href={`/resumes/${resume.id}/tailor?versionId=${selectedVersion.id}`}>
                      <Button size="sm" variant="outline" className="h-7 text-xs gap-1 border-primary/40 text-primary hover:bg-primary/10">
                        <Sparkles className="h-3 w-3" /> Tailor
                      </Button>
                    </Link>
                    {resume.active_version_id === selectedVersion.id ? (
                      <Badge className="bg-primary/90 text-xs">Active Version</Badge>
                    ) : (
                      selectedVersion.status === "READY" && (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => activateVersion(selectedVersion.id)}
                          disabled={isActivating}
                          className="h-7 text-xs"
                        >
                          Designate as Active
                        </Button>
                      )
                    )}
                  </div>
                </div>

                {selectedVersion.change_summary && (
                  <div className="p-2 rounded bg-muted/50 text-xs mt-3 text-muted-foreground">
                    <span className="font-medium text-foreground">Summary: </span>
                    {selectedVersion.change_summary}
                  </div>
                )}
              </CardHeader>

              <CardContent className="p-5 flex-1 flex flex-col">
                <div className="text-xs font-semibold uppercase text-muted-foreground mb-2 flex items-center justify-between">
                  <span>Extracted Text Content</span>
                  {selectedVersion.file_path && (
                    <span className="font-mono text-[10px] text-muted-foreground truncate max-w-[200px]">
                      {selectedVersion.file_path.split("/").pop()}
                    </span>
                  )}
                </div>

                {selectedVersion.status === "FAILED" ? (
                  <div className="p-4 rounded-lg bg-destructive/10 border border-destructive/20 text-destructive text-sm">
                    <div className="font-semibold flex items-center gap-1.5">
                      <AlertCircle className="h-4 w-4" /> Extraction Error
                    </div>
                    <p className="text-xs mt-1">
                      {selectedVersion.error_detail || "Document extraction encountered an issue."}
                    </p>
                  </div>
                ) : selectedVersion.extracted_text ? (
                  <div className="flex-1 bg-muted/30 border rounded-md p-4 font-mono text-xs whitespace-pre-wrap leading-relaxed overflow-y-auto max-h-[500px]">
                    {selectedVersion.extracted_text}
                  </div>
                ) : (
                  <div className="flex-1 border rounded-md p-8 flex flex-col items-center justify-center text-center text-muted-foreground">
                    <FileText className="h-8 w-8 mb-2 opacity-50" />
                    <p className="text-xs">No extracted plain text is attached to this version.</p>
                  </div>
                )}
              </CardContent>
            </Card>
          ) : (
            <Card className="h-full flex items-center justify-center p-8 text-center text-muted-foreground text-xs">
              Select a version from the timeline to inspect its snapshot.
            </Card>
          )}
        </div>
      </div>

      {/* UPLOAD VERSION MODAL */}
      <Dialog open={uploadModalOpen} onOpenChange={setUploadModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Upload New Resume Version</DialogTitle>
            <DialogDescription>
              Upload a .pdf or .docx resume document. ResumeForge will extract text and record a new immutable version.
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleUploadSubmit} className="space-y-4">
            <div className="space-y-1">
              <label className="text-xs font-medium">Select File (.pdf, .docx) *</label>
              <Input
                type="file"
                accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                onChange={handleFileChange}
                required
              />
            </div>

            {uploadError && (
              <div className="text-xs text-destructive p-2 rounded bg-destructive/10 flex items-center gap-1.5">
                <AlertCircle className="h-3.5 w-3.5" />
                {uploadError}
              </div>
            )}

            <div className="space-y-1">
              <label className="text-xs font-medium">Version Number *</label>
              <Input
                placeholder="e.g. v1.1 or v2.0"
                value={uploadVersionNumber}
                onChange={(e) => setUploadVersionNumber(e.target.value)}
                required
              />
            </div>

            <div className="space-y-1">
              <label className="text-xs font-medium">Change Summary Note</label>
              <Textarea
                rows={2}
                placeholder="e.g. Added cloud certifications, tailored for backend role..."
                value={uploadSummary}
                onChange={(e) => setUploadSummary(e.target.value)}
              />
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setUploadModalOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={isUploading || !uploadFile}>
                {isUploading ? "Uploading & Extracting..." : "Upload & Save Version"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* CLONE VERSION MODAL */}
      <Dialog open={cloneModalOpen} onOpenChange={setCloneModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Clone Version</DialogTitle>
            <DialogDescription>
              Create a new version branched from {targetCloneVersion?.version_number}.
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleCloneSubmit} className="space-y-4">
            <div className="space-y-1">
              <label className="text-xs font-medium">New Version Number *</label>
              <Input
                value={cloneVersionNumber}
                onChange={(e) => setCloneVersionNumber(e.target.value)}
                required
              />
            </div>

            <div className="space-y-1">
              <label className="text-xs font-medium">Change Summary</label>
              <Textarea
                rows={2}
                value={cloneSummary}
                onChange={(e) => setCloneSummary(e.target.value)}
              />
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setCloneModalOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={isCloning}>
                {isCloning ? "Cloning..." : "Create Cloned Version"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}

