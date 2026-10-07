"use client";

import { useState } from "react";
import Link from "next/link";
import { FileText, Plus, Upload, Trash2, ArrowRight } from "lucide-react";
import { toast } from "sonner";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { EmptyState } from "@/components/shared/empty-state";
import { useResumes } from "@/lib/hooks/use-resumes";

export default function ResumesPage() {
  const { resumes, isLoading, isError, createResume, isCreating, deleteResume } = useResumes();
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [selectedResumeId, setSelectedResumeId] = useState<string | null>(null);
  const [form, setForm] = useState({ title: "", target_role: "" });

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.title.trim()) return;
    try {
      await createResume({
        title: form.title.trim(),
        target_role: form.target_role.trim() || undefined,
      });
      toast.success("Resume created successfully");
      setCreateModalOpen(false);
      setForm({ title: "", target_role: "" });
    } catch (err: any) {
      toast.error(err?.message || "Failed to create resume");
    }
  };

  const handleDelete = async () => {
    if (!selectedResumeId) return;
    try {
      await deleteResume(selectedResumeId);
      toast.success("Resume deleted");
      setDeleteModalOpen(false);
      setSelectedResumeId(null);
    } catch (err: any) {
      toast.error(err?.message || "Failed to delete resume");
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Resumes</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            All your targeted, version-controlled resumes in one place.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Link href="/resumes/upload">
            <Button variant="outline" className="gap-1.5">
              <Upload className="h-4 w-4" />
              Upload Resume
            </Button>
          </Link>
          <Button onClick={() => setCreateModalOpen(true)} className="gap-1.5">
            <Plus className="h-4 w-4" />
            Create Blank
          </Button>
        </div>
      </div>

      {isLoading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <Card key={i} className="animate-pulse h-44 bg-muted/30" />
          ))}
        </div>
      ) : isError ? (
        <Card className="p-8 text-center border-destructive/20 bg-destructive/5">
          <p className="text-sm text-destructive">Failed to load resumes. Ensure backend is running.</p>
        </Card>
      ) : resumes.length === 0 ? (
        <EmptyState
          icon={FileText}
          title="No resumes yet"
          description="Upload an existing resume (PDF/DOCX) or create a blank one to get started."
          action={{ label: "Upload Resume", href: "/resumes/upload" }}
        />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {resumes.map((resume) => (
            <Card key={resume.id} className="flex flex-col justify-between hover:border-accent/40 transition-colors">
              <CardHeader>
                <div className="flex items-start justify-between gap-2">
                  <div className="space-y-1">
                    <CardTitle className="text-base line-clamp-1">{resume.title}</CardTitle>
                    <CardDescription className="text-xs">
                      {resume.target_role || "General Purpose"}
                    </CardDescription>
                  </div>
                  <Badge variant="outline" className="font-mono text-xs">
                    v{resume.versions?.[0]?.version_number || "1.0"}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="text-xs text-muted-foreground">
                <p>Created: {new Date(resume.created_at).toLocaleDateString()}</p>
                <p className="mt-1">
                  Updated: {new Date(resume.updated_at).toLocaleDateString()}
                </p>
              </CardContent>
              <CardFooter className="pt-2 flex items-center justify-between border-t border-border/50">
                <Button
                  variant="ghost"
                  size="sm"
                  className="text-destructive hover:text-destructive text-xs"
                  onClick={() => {
                    setSelectedResumeId(resume.id);
                    setDeleteModalOpen(true);
                  }}
                >
                  <Trash2 className="h-3.5 w-3.5 mr-1" /> Delete
                </Button>
                <Link href={`/resumes/${resume.id}`}>
                  <Button size="sm" variant="secondary" className="text-xs gap-1">
                    View Details <ArrowRight className="h-3.5 w-3.5" />
                  </Button>
                </Link>
              </CardFooter>
            </Card>
          ))}
        </div>
      )}

      {/* Create Modal */}
      <Dialog open={createModalOpen} onOpenChange={setCreateModalOpen}>
        <DialogContent>
          <form onSubmit={handleCreate} className="space-y-4">
            <DialogHeader>
              <DialogTitle>Create New Resume</DialogTitle>
              <DialogDescription>
                Start a new targeted resume version from your Master Career Profile.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-3">
              <div>
                <label className="text-xs font-medium">Resume Title *</label>
                <Input
                  placeholder="e.g. Senior Backend Engineer - Python"
                  value={form.title}
                  onChange={(e) => setForm({ ...form, title: e.target.value })}
                  required
                />
              </div>
              <div>
                <label className="text-xs font-medium">Target Role</label>
                <Input
                  placeholder="e.g. Staff Software Engineer"
                  value={form.target_role}
                  onChange={(e) => setForm({ ...form, target_role: e.target.value })}
                />
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setCreateModalOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={isCreating || !form.title.trim()}>
                {isCreating ? "Creating..." : "Create Resume"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Modal */}
      <Dialog open={deleteModalOpen} onOpenChange={setDeleteModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Resume</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete this resume and all its version history? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={handleDelete}>
              Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
