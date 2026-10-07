"use client";

import { useState } from "react";
import Link from "next/link";
import { Briefcase, Sparkles, Trash2, ArrowRight } from "lucide-react";
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
import { EmptyState } from "@/components/shared/empty-state";
import { useJobs } from "@/lib/hooks/use-jobs";

export default function JobsPage() {
  const { jobs, isLoading, isError, deleteJob } = useJobs();
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null);

  const handleDelete = async () => {
    if (!selectedJobId) return;
    try {
      await deleteJob(selectedJobId);
      toast.success("Job description deleted");
      setDeleteModalOpen(false);
      setSelectedJobId(null);
    } catch (err: any) {
      toast.error(err?.message || "Failed to delete job");
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Job Descriptions</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Analyze requirements and match them against your master profile and resumes.
          </p>
        </div>
        <Link href="/jobs/new">
          <Button className="gap-1.5">
            <Sparkles className="h-4 w-4" />
            Analyze New Job
          </Button>
        </Link>
      </div>

      {isLoading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <Card key={i} className="animate-pulse h-44 bg-muted/30" />
          ))}
        </div>
      ) : isError ? (
        <Card className="p-8 text-center border-destructive/20 bg-destructive/5">
          <p className="text-sm text-destructive">Failed to load jobs. Ensure backend is running.</p>
        </Card>
      ) : jobs.length === 0 ? (
        <EmptyState
          icon={Briefcase}
          title="No job descriptions analyzed"
          description="Paste or upload a target job description to extract requirements and evaluate semantic match."
          action={{ label: "Analyze New Job", href: "/jobs/new" }}
        />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {jobs.map((job) => (
            <Card key={job.id} className="flex flex-col justify-between hover:border-accent/40 transition-colors">
              <CardHeader>
                <div className="flex items-start justify-between gap-2">
                  <div className="space-y-1">
                    <CardTitle className="text-base line-clamp-1">{job.title}</CardTitle>
                    <CardDescription className="text-xs">
                      {job.company || "Target Company"}
                    </CardDescription>
                  </div>
                  <Badge variant="outline" className="text-xs">
                    {job.skills?.length || 0} skills
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="text-xs text-muted-foreground space-y-1">
                <p>
                  Requirements:{" "}
                  <span className="font-medium text-foreground">
                    {job.requirements?.length || 0} identified
                  </span>
                </p>
                <p>
                  Analyzed on: {new Date(job.created_at).toLocaleDateString()}
                </p>
              </CardContent>
              <CardFooter className="pt-2 flex items-center justify-between border-t border-border/50">
                <Button
                  variant="ghost"
                  size="sm"
                  className="text-destructive hover:text-destructive text-xs"
                  onClick={() => {
                    setSelectedJobId(job.id);
                    setDeleteModalOpen(true);
                  }}
                >
                  <Trash2 className="h-3.5 w-3.5 mr-1" /> Delete
                </Button>
                <Link href={`/jobs/${job.id}`}>
                  <Button size="sm" variant="secondary" className="text-xs gap-1">
                    Match & Tailor <ArrowRight className="h-3.5 w-3.5" />
                  </Button>
                </Link>
              </CardFooter>
            </Card>
          ))}
        </div>
      )}

      {/* Delete Confirmation Modal */}
      <Dialog open={deleteModalOpen} onOpenChange={setDeleteModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Job Description</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete this job description and its match history? This action cannot be undone.
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
