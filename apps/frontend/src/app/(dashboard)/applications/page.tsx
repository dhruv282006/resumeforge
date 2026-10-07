"use client";

import { useState } from "react";
import Link from "next/link";
import {
  ClipboardList,
  Plus,
  Trash2,
  Building,
  MapPin,
  DollarSign,
  ExternalLink,
  Clock,
} from "lucide-react";
import { toast } from "sonner";
import {
  Card,
  CardContent,
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
import { Textarea } from "@/components/ui/textarea";
import { EmptyState } from "@/components/shared/empty-state";
import { useApplications } from "@/lib/hooks/use-applications";
import { useResumes } from "@/lib/hooks/use-resumes";
import { useJobs } from "@/lib/hooks/use-jobs";

const STAGES = [
  { key: "ALL", label: "All" },
  { key: "APPLIED", label: "Applied" },
  { key: "SCREENING", label: "Screening" },
  { key: "INTERVIEWING", label: "Interviewing" },
  { key: "OFFERED", label: "Offered" },
  { key: "REJECTED", label: "Rejected" },
];

function getStatusBadge(status: string) {
  switch (status.toUpperCase()) {
    case "OFFERED":
      return <Badge className="bg-emerald-600 hover:bg-emerald-700 text-white">Offered</Badge>;
    case "INTERVIEWING":
      return <Badge className="bg-blue-600 hover:bg-blue-700 text-white">Interviewing</Badge>;
    case "SCREENING":
      return <Badge className="bg-amber-600 hover:bg-amber-700 text-white">Screening</Badge>;
    case "REJECTED":
      return <Badge variant="destructive">Rejected</Badge>;
    case "WITHDRAWN":
      return <Badge variant="outline">Withdrawn</Badge>;
    case "APPLIED":
    default:
      return <Badge variant="secondary">Applied</Badge>;
  }
}

export default function ApplicationsPage() {
  const [selectedTab, setSelectedTab] = useState<string>("ALL");
  const filterParam = selectedTab === "ALL" ? undefined : selectedTab;
  const {
    applications,
    stats,
    isLoading,
    isError,
    createApplication,
    isCreating,
    updateApplication,
    deleteApplication,
  } = useApplications(filterParam);

  const { resumes } = useResumes();
  const { jobs } = useJobs();

  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [selectedAppId, setSelectedAppId] = useState<string | null>(null);

  const [form, setForm] = useState({
    company: "",
    position: "",
    status: "APPLIED",
    location: "",
    salary_range: "",
    job_url: "",
    notes: "",
    resume_id: "",
    job_id: "",
  });

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.company.trim() || !form.position.trim()) return;

    try {
      await createApplication({
        company: form.company.trim(),
        position: form.position.trim(),
        status: form.status,
        location: form.location.trim() || undefined,
        salary_range: form.salary_range.trim() || undefined,
        job_url: form.job_url.trim() || undefined,
        notes: form.notes.trim() || undefined,
        resume_id: form.resume_id || undefined,
        job_id: form.job_id || undefined,
      });
      toast.success("Application logged successfully");
      setCreateModalOpen(false);
      setForm({
        company: "",
        position: "",
        status: "APPLIED",
        location: "",
        salary_range: "",
        job_url: "",
        notes: "",
        resume_id: "",
        job_id: "",
      });
    } catch (err: any) {
      toast.error(err?.message || "Failed to log application");
    }
  };

  const handleStageChange = async (appId: string, newStatus: string) => {
    try {
      await updateApplication({
        id: appId,
        payload: { status: newStatus },
      });
      toast.success(`Application stage updated to ${newStatus.toLowerCase()}`);
    } catch (err: any) {
      toast.error(err?.message || "Failed to update stage");
    }
  };

  const handleDelete = async () => {
    if (!selectedAppId) return;
    try {
      await deleteApplication(selectedAppId);
      toast.success("Application deleted");
      setDeleteModalOpen(false);
      setSelectedAppId(null);
    } catch (err: any) {
      toast.error(err?.message || "Failed to delete application");
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Applications Tracker</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Track every job application, interview stage, and linked resume version.
          </p>
        </div>
        <Button onClick={() => setCreateModalOpen(true)} className="gap-1.5">
          <Plus className="h-4 w-4" />
          Log Application
        </Button>
      </div>

      <div className="grid gap-3 grid-cols-2 sm:grid-cols-3 lg:grid-cols-6">
        <Card className="p-3 text-center">
          <div className="text-xs text-muted-foreground">Total</div>
          <div className="text-2xl font-bold font-mono mt-1">{stats?.total ?? 0}</div>
        </Card>
        <Card className="p-3 text-center">
          <div className="text-xs text-muted-foreground">Applied</div>
          <div className="text-2xl font-bold font-mono mt-1">{stats?.applied ?? 0}</div>
        </Card>
        <Card className="p-3 text-center">
          <div className="text-xs text-muted-foreground">Screening</div>
          <div className="text-2xl font-bold font-mono mt-1 text-amber-500">{stats?.screening ?? 0}</div>
        </Card>
        <Card className="p-3 text-center">
          <div className="text-xs text-muted-foreground">Interviewing</div>
          <div className="text-2xl font-bold font-mono mt-1 text-blue-500">{stats?.interviewing ?? 0}</div>
        </Card>
        <Card className="p-3 text-center">
          <div className="text-xs text-muted-foreground">Offered</div>
          <div className="text-2xl font-bold font-mono mt-1 text-emerald-500">{stats?.offered ?? 0}</div>
        </Card>
        <Card className="p-3 text-center">
          <div className="text-xs text-muted-foreground">Rejected</div>
          <div className="text-2xl font-bold font-mono mt-1 text-rose-500">{stats?.rejected ?? 0}</div>
        </Card>
      </div>

      <div className="flex flex-wrap gap-2 border-b border-border pb-3">
        {STAGES.map((s) => (
          <Button
            key={s.key}
            variant={selectedTab === s.key ? "default" : "ghost"}
            size="sm"
            className="text-xs"
            onClick={() => setSelectedTab(s.key)}
          >
            {s.label}
          </Button>
        ))}
      </div>

      {isLoading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <Card key={i} className="animate-pulse h-28 bg-muted/30" />
          ))}
        </div>
      ) : isError ? (
        <Card className="p-8 text-center border-destructive/20 bg-destructive/5">
          <p className="text-sm text-destructive">Failed to load applications. Ensure backend is running.</p>
        </Card>
      ) : applications.length === 0 ? (
        <EmptyState
          icon={ClipboardList}
          title={selectedTab === "ALL" ? "No applications tracked" : `No applications in ${selectedTab.toLowerCase()}`}
          description="Log applications to monitor status, schedule interviews, and organize target resumes."
          action={{ label: "Log an Application", href: "/applications" }}
        />
      ) : (
        <div className="space-y-3">
          {applications.map((app) => (
            <Card key={app.id} className="hover:border-accent/40 transition-colors">
              <CardContent className="pt-5 pb-4">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                  <div className="space-y-1.5 flex-1">
                    <div className="flex items-center gap-2.5 flex-wrap">
                      <h3 className="font-semibold text-base">{app.position}</h3>
                      <span className="text-sm font-medium text-muted-foreground flex items-center gap-1">
                        at <Building className="h-3.5 w-3.5" /> {app.company}
                      </span>
                      {getStatusBadge(app.status)}
                    </div>
                    <div className="flex items-center gap-4 text-xs text-muted-foreground flex-wrap">
                      {app.location && (
                        <span className="flex items-center gap-1">
                          <MapPin className="h-3.5 w-3.5" /> {app.location}
                        </span>
                      )}
                      {app.salary_range && (
                        <span className="flex items-center gap-1">
                          <DollarSign className="h-3.5 w-3.5" /> {app.salary_range}
                        </span>
                      )}
                      {app.applied_date && (
                        <span className="flex items-center gap-1">
                          <Clock className="h-3.5 w-3.5" /> Applied on {app.applied_date}
                        </span>
                      )}
                      {app.job_url && (
                        <a
                          href={app.job_url}
                          target="_blank"
                          rel="noreferrer"
                          className="flex items-center gap-1 text-primary hover:underline"
                        >
                          <ExternalLink className="h-3 w-3" /> Job Link
                        </a>
                      )}
                    </div>
                    {app.notes && (
                      <p className="text-xs text-muted-foreground/90 italic bg-muted/30 p-2 rounded max-w-xl">
                        {app.notes}
                      </p>
                    )}
                  </div>

                  <div className="flex items-center gap-2 self-end md:self-center">
                    <select
                      className="text-xs border rounded-md px-2 py-1.5 bg-background font-medium focus:ring-1 focus:ring-accent"
                      value={app.status.toUpperCase()}
                      onChange={(e) => handleStageChange(app.id, e.target.value)}
                    >
                      <option value="APPLIED">Applied</option>
                      <option value="SCREENING">Screening</option>
                      <option value="INTERVIEWING">Interviewing</option>
                      <option value="OFFERED">Offered</option>
                      <option value="REJECTED">Rejected</option>
                      <option value="WITHDRAWN">Withdrawn</option>
                    </select>

                    <Button
                      variant="ghost"
                      size="sm"
                      className="text-destructive hover:text-destructive h-8 px-2"
                      onClick={() => {
                        setSelectedAppId(app.id);
                        setDeleteModalOpen(true);
                      }}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      <Dialog open={createModalOpen} onOpenChange={setCreateModalOpen}>
        <DialogContent className="max-w-md">
          <form onSubmit={handleCreate} className="space-y-4">
            <DialogHeader>
              <DialogTitle>Log Job Application</DialogTitle>
              <DialogDescription>
                Track your progress for a new job opportunity.
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-medium">Company *</label>
                  <Input
                    placeholder="e.g. Google"
                    value={form.company}
                    onChange={(e) => setForm({ ...form, company: e.target.value })}
                    required
                  />
                </div>
                <div>
                  <label className="text-xs font-medium">Position *</label>
                  <Input
                    placeholder="e.g. Senior Software Engineer"
                    value={form.position}
                    onChange={(e) => setForm({ ...form, position: e.target.value })}
                    required
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-medium">Stage</label>
                  <select
                    className="w-full text-xs border rounded-md px-3 py-2 bg-background"
                    value={form.status}
                    onChange={(e) => setForm({ ...form, status: e.target.value })}
                  >
                    <option value="APPLIED">Applied</option>
                    <option value="SCREENING">Screening</option>
                    <option value="INTERVIEWING">Interviewing</option>
                    <option value="OFFERED">Offered</option>
                    <option value="REJECTED">Rejected</option>
                    <option value="WITHDRAWN">Withdrawn</option>
                  </select>
                </div>
                <div>
                  <label className="text-xs font-medium">Location</label>
                  <Input
                    placeholder="e.g. Remote / NYC"
                    value={form.location}
                    onChange={(e) => setForm({ ...form, location: e.target.value })}
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-medium">Salary Range</label>
                  <Input
                    placeholder="e.g. $140k - $160k"
                    value={form.salary_range}
                    onChange={(e) => setForm({ ...form, salary_range: e.target.value })}
                  />
                </div>
                <div>
                  <label className="text-xs font-medium">Job Posting URL</label>
                  <Input
                    placeholder="https://..."
                    value={form.job_url}
                    onChange={(e) => setForm({ ...form, job_url: e.target.value })}
                  />
                </div>
              </div>

              {resumes.length > 0 && (
                <div>
                  <label className="text-xs font-medium">Linked Resume</label>
                  <select
                    className="w-full text-xs border rounded-md px-3 py-2 bg-background"
                    value={form.resume_id}
                    onChange={(e) => setForm({ ...form, resume_id: e.target.value })}
                  >
                    <option value="">None</option>
                    {resumes.map((r) => (
                      <option key={r.id} value={r.id}>
                        {r.title}
                      </option>
                    ))}
                  </select>
                </div>
              )}

              {jobs.length > 0 && (
                <div>
                  <label className="text-xs font-medium">Linked Job Description</label>
                  <select
                    className="w-full text-xs border rounded-md px-3 py-2 bg-background"
                    value={form.job_id}
                    onChange={(e) => setForm({ ...form, job_id: e.target.value })}
                  >
                    <option value="">None</option>
                    {jobs.map((j) => (
                      <option key={j.id} value={j.id}>
                        {j.title} ({j.company || "Company"})
                      </option>
                    ))}
                  </select>
                </div>
              )}

              <div>
                <label className="text-xs font-medium">Notes</label>
                <Textarea
                  placeholder="Notes, recruiter contacts, follow-up dates..."
                  value={form.notes}
                  onChange={(e) => setForm({ ...form, notes: e.target.value })}
                  rows={2}
                />
              </div>
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setCreateModalOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={isCreating || !form.company.trim() || !form.position.trim()}>
                {isCreating ? "Logging..." : "Log Application"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      <Dialog open={deleteModalOpen} onOpenChange={setDeleteModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Application</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete this tracked application?
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
