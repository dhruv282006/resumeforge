"use client";

import * as React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowLeft, FileUp, Upload, CheckCircle2, AlertCircle, FileText } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { useResumes, useResumeDetail } from "@/lib/hooks/use-resumes";
import { toast } from "sonner";

export default function ResumeUploadPage() {
  const router = useRouter();
  const { createResume, isCreating } = useResumes();

  const [file, setFile] = React.useState<File | null>(null);
  const [title, setTitle] = React.useState("");
  const [targetRole, setTargetRole] = React.useState("");
  const [targetCompany, setTargetCompany] = React.useState("");
  const [description, setDescription] = React.useState("");
  const [isProcessing, setIsProcessing] = React.useState(false);
  const [errorMessage, setErrorMessage] = React.useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setErrorMessage(null);
    const selectedFile = e.target.files?.[0];
    if (!selectedFile) return;

    const lower = selectedFile.name.toLowerCase();
    if (!lower.endsWith(".pdf") && !lower.endsWith(".docx")) {
      setErrorMessage("Unsupported file format. Please upload a .pdf or .docx file.");
      return;
    }

    if (selectedFile.size > 10 * 1024 * 1024) {
      setErrorMessage("File exceeds 10MB maximum limit.");
      return;
    }

    setFile(selectedFile);
    if (!title) {
      const cleanTitle = selectedFile.name.replace(/\.[^/.]+$/, "").replace(/[-_]/g, " ");
      setTitle(cleanTitle);
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setErrorMessage(null);
    const droppedFile = e.dataTransfer.files?.[0];
    if (!droppedFile) return;

    const lower = droppedFile.name.toLowerCase();
    if (!lower.endsWith(".pdf") && !lower.endsWith(".docx")) {
      setErrorMessage("Unsupported file format. Please upload a .pdf or .docx file.");
      return;
    }

    if (droppedFile.size > 10 * 1024 * 1024) {
      setErrorMessage("File exceeds 10MB maximum limit.");
      return;
    }

    setFile(droppedFile);
    if (!title) {
      const cleanTitle = droppedFile.name.replace(/\.[^/.]+$/, "").replace(/[-_]/g, " ");
      setTitle(cleanTitle);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      setErrorMessage("Please select a resume file (.pdf or .docx) to upload.");
      return;
    }

    setIsProcessing(true);
    setErrorMessage(null);

    try {
      // 1. Create the resume family
      const resume = await createResume({
        title: title.trim() || file.name,
        target_role: targetRole.trim() || undefined,
        target_company: targetCompany.trim() || undefined,
        description: description.trim() || undefined,
      });

      // 2. Upload the file to become the active version
      const baseUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
      const formData = new FormData();
      formData.append("file", file);
      formData.append("version_number", "v1.0");
      formData.append("change_summary", `Uploaded ${file.name}`);

      const uploadResp = await fetch(
        `${baseUrl.replace(/\/$/, "")}/api/v1/resumes/${resume.id}/versions/upload`,
        {
          method: "POST",
          body: formData,
        }
      );

      if (!uploadResp.ok) {
        let errDetail = `Upload failed with status ${uploadResp.status}`;
        try {
          const parsed = await uploadResp.json();
          if (parsed.detail) errDetail = typeof parsed.detail === "string" ? parsed.detail : JSON.stringify(parsed.detail);
        } catch {
          // ignore
        }
        throw new Error(errDetail);
      }

      toast.success(`Resume "${resume.title}" uploaded and parsed successfully!`);
      router.push(`/resumes/${resume.id}`);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to upload and process resume.";
      setErrorMessage(msg);
      toast.error(msg);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="space-y-6 max-w-3xl mx-auto">
      {/* Back button */}
      <div>
        <Button variant="ghost" size="sm" asChild className="mb-2 -ml-2 text-xs">
          <Link href="/resumes">
            <ArrowLeft className="h-3.5 w-3.5 mr-1" /> Back to Resumes
          </Link>
        </Button>
        <h1 className="text-2xl font-bold tracking-tight">Upload New Resume</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Upload a PDF or DOCX resume. ResumeForge will extract text, parse structure, and create version v1.0.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Dropzone Card */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Document File</CardTitle>
            <CardDescription className="text-xs">
              Supports .pdf and .docx documents up to 10MB.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div
              onDragOver={(e) => e.preventDefault()}
              onDrop={handleDrop}
              className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
                file ? "border-primary bg-primary/5" : "border-border hover:border-primary/50"
              }`}
            >
              <input
                id="resume-file-input"
                type="file"
                accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                onChange={handleFileChange}
                className="hidden"
              />

              {file ? (
                <div className="flex flex-col items-center">
                  <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center text-primary mb-3">
                    <FileText className="h-6 w-6" />
                  </div>
                  <p className="font-semibold text-sm">{file.name}</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    {(file.size / 1024).toFixed(1)} KB • Ready to parse
                  </p>
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    className="mt-4 text-xs"
                    onClick={() => document.getElementById("resume-file-input")?.click()}
                  >
                    Change File
                  </Button>
                </div>
              ) : (
                <div className="flex flex-col items-center">
                  <div className="h-12 w-12 rounded-full bg-muted flex items-center justify-center text-muted-foreground mb-3">
                    <Upload className="h-6 w-6" />
                  </div>
                  <p className="text-sm font-medium">Drag & drop your resume file here</p>
                  <p className="text-xs text-muted-foreground mt-1 mb-4">
                    PDF or DOCX format (max 10MB)
                  </p>
                  <Button
                    type="button"
                    variant="secondary"
                    size="sm"
                    className="text-xs"
                    onClick={() => document.getElementById("resume-file-input")?.click()}
                  >
                    Browse Local Files
                  </Button>
                </div>
              )}
            </div>

            {errorMessage && (
              <div className="mt-3 p-3 rounded-lg bg-destructive/10 text-destructive text-xs flex items-center gap-2">
                <AlertCircle className="h-4 w-4 shrink-0" />
                <span>{errorMessage}</span>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Resume Metadata Card */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Resume Details</CardTitle>
            <CardDescription className="text-xs">
              Label and target direction for this resume family.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-1">
              <label className="text-xs font-medium">Resume Title *</label>
              <Input
                placeholder="e.g. Senior Backend Engineer Resume"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                required
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-1">
                <label className="text-xs font-medium">Target Role</label>
                <Input
                  placeholder="e.g. Distributed Systems Engineer"
                  value={targetRole}
                  onChange={(e) => setTargetRole(e.target.value)}
                />
              </div>
              <div className="space-y-1">
                <label className="text-xs font-medium">Target Company</label>
                <Input
                  placeholder="e.g. Stripe, AWS, Meta"
                  value={targetCompany}
                  onChange={(e) => setTargetCompany(e.target.value)}
                />
              </div>
            </div>

            <div className="space-y-1">
              <label className="text-xs font-medium">Notes / Purpose</label>
              <Textarea
                rows={2}
                placeholder="Optional notes or context for this resume version..."
                value={description}
                onChange={(e) => setDescription(e.target.value)}
              />
            </div>
          </CardContent>
        </Card>

        {/* Submit Actions */}
        <div className="flex items-center justify-end gap-3">
          <Button variant="outline" asChild disabled={isProcessing}>
            <Link href="/resumes">Cancel</Link>
          </Button>
          <Button type="submit" disabled={isProcessing || !file || isCreating}>
            <FileUp className="h-4 w-4 mr-1.5" />
            {isProcessing ? "Uploading & Extracting..." : "Upload & Parse Resume"}
          </Button>
        </div>
      </form>
    </div>
  );
}
