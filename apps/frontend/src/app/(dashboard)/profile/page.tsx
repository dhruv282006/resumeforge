"use client";

import * as React from "react";
import {
  Award,
  Briefcase,
  FolderGit2,
  GraduationCap,
  Plus,
  Trash2,
  User,
  Wrench,
  CheckCircle2,
  ExternalLink,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
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
import { EmptyState } from "@/components/shared/empty-state";
import { useProfile } from "@/lib/hooks/use-profile";
import type {
  CertificationItem,
  EducationItem,
  ExperienceItem,
  ProjectItem,
  SkillItem,
} from "@/types/profile";

export default function ProfilePage() {
  const {
    profile,
    isLoading,
    isError,
    refetch,
    completeness,
    updateProfile,
    isUpdatingProfile,
    addEducation,
    deleteEducation,
    addExperience,
    deleteExperience,
    addSkill,
    deleteSkill,
    addProject,
    deleteProject,
    addCertification,
    deleteCertification,
  } = useProfile();

  // Dialog state
  const [eduModalOpen, setEduModalOpen] = React.useState(false);
  const [expModalOpen, setExpModalOpen] = React.useState(false);
  const [skillModalOpen, setSkillModalOpen] = React.useState(false);
  const [projModalOpen, setProjModalOpen] = React.useState(false);
  const [certModalOpen, setCertModalOpen] = React.useState(false);

  // Profile Form state
  const [fullName, setFullName] = React.useState("");
  const [headline, setHeadline] = React.useState("");
  const [summary, setSummary] = React.useState("");
  const [email, setEmail] = React.useState("");
  const [phone, setPhone] = React.useState("");
  const [location, setLocation] = React.useState("");
  const [linkedinUrl, setLinkedinUrl] = React.useState("");
  const [githubUrl, setGithubUrl] = React.useState("");
  const [portfolioUrl, setPortfolioUrl] = React.useState("");
  const [preferredRoles, setPreferredRoles] = React.useState("");
  const [yoe, setYoe] = React.useState<number | "">("");

  // Populate form when profile loads
  React.useEffect(() => {
    if (profile) {
      setFullName(profile.full_name || "");
      setHeadline(profile.headline || "");
      setSummary(profile.summary || "");
      setEmail(profile.email || "");
      setPhone(profile.phone || "");
      setLocation(profile.location || "");
      setLinkedinUrl(profile.linkedin_url || "");
      setGithubUrl(profile.github_url || "");
      setPortfolioUrl(profile.portfolio_url || "");
      setPreferredRoles((profile.preferred_roles || []).join(", "));
      setYoe(profile.years_of_experience ?? "");
    }
  }, [profile]);

  // Form states for modals
  const [eduForm, setEduForm] = React.useState<Omit<EducationItem, "id">>({
    institution: "",
    degree: "",
    field_of_study: "",
    start_date: "",
    end_date: "",
    gpa: undefined,
  });

  const [expForm, setExpForm] = React.useState<Omit<ExperienceItem, "id">>({
    company: "",
    title: "",
    location: "",
    start_date: "",
    end_date: "",
    is_current: false,
    description: "",
    achievements: [],
  });
  const [achievementsText, setAchievementsText] = React.useState("");

  const [skillForm, setSkillForm] = React.useState<Omit<SkillItem, "id">>({
    name: "",
    category: "TECHNICAL",
    proficiency: "PROFICIENT",
    source: "USER_PROVIDED",
    years_of_experience: undefined,
  });

  const [projForm, setProjForm] = React.useState<Omit<ProjectItem, "id">>({
    name: "",
    role: "",
    description: "",
    technologies: [],
    project_url: "",
    github_url: "",
  });
  const [techText, setTechText] = React.useState("");

  const [certForm, setCertForm] = React.useState<Omit<CertificationItem, "id">>({
    name: "",
    issuing_organization: "",
    issue_date: "",
    expiry_date: "",
    credential_id: "",
    credential_url: "",
  });

  if (isLoading) {
    return <LoadingState message="Loading Master Career Profile..." />;
  }

  if (isError || !profile) {
    return (
      <ErrorState
        title="Failed to load profile"
        message="Could not retrieve your master profile. Please ensure the backend server is running."
        onRetry={() => refetch()}
      />
    );
  }

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    await updateProfile({
      full_name: fullName,
      headline,
      summary,
      email,
      phone,
      location,
      linkedin_url: linkedinUrl,
      github_url: githubUrl,
      portfolio_url: portfolioUrl,
      preferred_roles: preferredRoles
        ? preferredRoles.split(",").map((r) => r.trim()).filter(Boolean)
        : [],
      years_of_experience: typeof yoe === "number" ? yoe : undefined,
    });
  };

  const handleAddEducation = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!eduForm.institution) return;
    await addEducation(eduForm);
    setEduModalOpen(false);
    setEduForm({ institution: "", degree: "", field_of_study: "", start_date: "", end_date: "" });
  };

  const handleAddExperience = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!expForm.company || !expForm.title) return;
    const achievements = achievementsText
      .split("\n")
      .map((a) => a.trim())
      .filter(Boolean);
    await addExperience({ ...expForm, achievements });
    setExpModalOpen(false);
    setExpForm({ company: "", title: "", is_current: false, description: "", achievements: [] });
    setAchievementsText("");
  };

  const handleAddSkill = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!skillForm.name) return;
    await addSkill(skillForm);
    setSkillModalOpen(false);
    setSkillForm({ name: "", category: "TECHNICAL", proficiency: "PROFICIENT", source: "USER_PROVIDED" });
  };

  const handleAddProject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!projForm.name) return;
    const technologies = techText.split(",").map((t) => t.trim()).filter(Boolean);
    await addProject({ ...projForm, technologies });
    setProjModalOpen(false);
    setProjForm({ name: "", role: "", description: "", technologies: [] });
    setTechText("");
  };

  const handleAddCertification = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!certForm.name) return;
    await addCertification(certForm);
    setCertModalOpen(false);
    setCertForm({ name: "", issuing_organization: "" });
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Master Career Profile</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Your single source of truth. All targeted resumes and job matches are grounded in this verified data.
        </p>
      </div>

      {/* Completeness Card */}
      {completeness && (
        <Card className="border-accent/20 bg-accent/5">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-base font-semibold flex items-center gap-2">
                  <CheckCircle2 className="h-5 w-5 text-accent" />
                  Profile Completeness
                </CardTitle>
                <CardDescription className="text-xs mt-0.5">
                  Internal deterministic scoring across career dimensions
                </CardDescription>
              </div>
              <span className="text-2xl font-bold text-accent">{completeness.overall}%</span>
            </div>
            <Progress value={completeness.overall} className="mt-2" />
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-7 gap-3 text-xs">
              <div className="p-2 rounded bg-card/60 border text-center">
                <div className="text-muted-foreground">Personal</div>
                <div className="font-semibold mt-1">{completeness.sections.personal}%</div>
              </div>
              <div className="p-2 rounded bg-card/60 border text-center">
                <div className="text-muted-foreground">Education</div>
                <div className="font-semibold mt-1">{completeness.sections.education}%</div>
              </div>
              <div className="p-2 rounded bg-card/60 border text-center">
                <div className="text-muted-foreground">Experience</div>
                <div className="font-semibold mt-1">{completeness.sections.experience}%</div>
              </div>
              <div className="p-2 rounded bg-card/60 border text-center">
                <div className="text-muted-foreground">Skills</div>
                <div className="font-semibold mt-1">{completeness.sections.skills}%</div>
              </div>
              <div className="p-2 rounded bg-card/60 border text-center">
                <div className="text-muted-foreground">Projects</div>
                <div className="font-semibold mt-1">{completeness.sections.projects}%</div>
              </div>
              <div className="p-2 rounded bg-card/60 border text-center">
                <div className="text-muted-foreground">Certifications</div>
                <div className="font-semibold mt-1">{completeness.sections.certifications}%</div>
              </div>
              <div className="p-2 rounded bg-card/60 border text-center">
                <div className="text-muted-foreground">Links</div>
                <div className="font-semibold mt-1">{completeness.sections.links}%</div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Tabs Layout */}
      <Tabs defaultValue="personal" className="w-full">
        <TabsList className="grid grid-cols-3 sm:grid-cols-6 h-auto p-1 bg-muted/60">
          <TabsTrigger value="personal" className="flex items-center gap-1.5 py-2">
            <User className="h-4 w-4" />
            <span>Personal</span>
          </TabsTrigger>
          <TabsTrigger value="experience" className="flex items-center gap-1.5 py-2">
            <Briefcase className="h-4 w-4" />
            <span>Experience</span>
          </TabsTrigger>
          <TabsTrigger value="education" className="flex items-center gap-1.5 py-2">
            <GraduationCap className="h-4 w-4" />
            <span>Education</span>
          </TabsTrigger>
          <TabsTrigger value="skills" className="flex items-center gap-1.5 py-2">
            <Wrench className="h-4 w-4" />
            <span>Skills</span>
          </TabsTrigger>
          <TabsTrigger value="projects" className="flex items-center gap-1.5 py-2">
            <FolderGit2 className="h-4 w-4" />
            <span>Projects</span>
          </TabsTrigger>
          <TabsTrigger value="certifications" className="flex items-center gap-1.5 py-2">
            <Award className="h-4 w-4" />
            <span>Certs</span>
          </TabsTrigger>
        </TabsList>

        {/* 1. PERSONAL INFORMATION & PREFERENCES */}
        <TabsContent value="personal" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Personal Information & Career Preferences</CardTitle>
              <CardDescription>
                Fundamental contact details and target career direction.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSaveProfile} className="space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="space-y-1">
                    <label className="text-xs font-medium">Full Name *</label>
                    <Input
                      value={fullName}
                      onChange={(e) => setFullName(e.target.value)}
                      required
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-xs font-medium">Professional Headline</label>
                    <Input
                      placeholder="e.g. Senior Backend Engineer | Distributed Systems"
                      value={headline}
                      onChange={(e) => setHeadline(e.target.value)}
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-xs font-medium">Email Address</label>
                    <Input
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-xs font-medium">Phone</label>
                    <Input
                      value={phone}
                      onChange={(e) => setPhone(e.target.value)}
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-xs font-medium">Location</label>
                    <Input
                      placeholder="e.g. San Francisco, CA or Remote"
                      value={location}
                      onChange={(e) => setLocation(e.target.value)}
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-xs font-medium">Years of Experience</label>
                    <Input
                      type="number"
                      step="0.5"
                      placeholder="e.g. 5.5"
                      value={yoe}
                      onChange={(e) => setYoe(e.target.value ? parseFloat(e.target.value) : "")}
                    />
                  </div>
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-medium">Professional Summary</label>
                  <Textarea
                    rows={4}
                    placeholder="Concise overview of your career, core competencies, and notable strengths..."
                    value={summary}
                    onChange={(e) => setSummary(e.target.value)}
                  />
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  <div className="space-y-1">
                    <label className="text-xs font-medium">LinkedIn URL</label>
                    <Input
                      placeholder="https://linkedin.com/in/..."
                      value={linkedinUrl}
                      onChange={(e) => setLinkedinUrl(e.target.value)}
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-xs font-medium">GitHub URL</label>
                    <Input
                      placeholder="https://github.com/..."
                      value={githubUrl}
                      onChange={(e) => setGithubUrl(e.target.value)}
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-xs font-medium">Portfolio URL</label>
                    <Input
                      placeholder="https://portfolio.dev"
                      value={portfolioUrl}
                      onChange={(e) => setPortfolioUrl(e.target.value)}
                    />
                  </div>
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-medium">Preferred Target Roles (comma separated)</label>
                  <Input
                    placeholder="Staff Backend Engineer, Distributed Systems Architect"
                    value={preferredRoles}
                    onChange={(e) => setPreferredRoles(e.target.value)}
                  />
                </div>

                <div className="flex justify-end pt-2">
                  <Button type="submit" disabled={isUpdatingProfile}>
                    {isUpdatingProfile ? "Saving..." : "Save Profile Details"}
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </TabsContent>

        {/* 2. EXPERIENCE */}
        <TabsContent value="experience" className="space-y-4">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-lg font-semibold">Work Experience</h2>
              <p className="text-xs text-muted-foreground">
                Documented career history. In later phases, AI recommendations are strictly grounded in these entries.
              </p>
            </div>
            <Button size="sm" onClick={() => setExpModalOpen(true)} className="gap-1">
              <Plus className="h-4 w-4" /> Add Experience
            </Button>
          </div>

          {(!profile.experiences || profile.experiences.length === 0) ? (
            <EmptyState
              title="No work experience added"
              description="Add your current and past professional roles to build your profile."
            />
          ) : (
            <div className="space-y-3">
              {profile.experiences.map((exp) => (
                <Card key={exp.id}>
                  <CardHeader className="p-4 pb-2">
                    <div className="flex items-start justify-between">
                      <div>
                        <CardTitle className="text-base font-semibold">{exp.title}</CardTitle>
                        <CardDescription className="text-sm font-medium text-foreground">
                          {exp.company} {exp.location && `• ${exp.location}`}
                        </CardDescription>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-destructive h-8 w-8 p-0"
                        onClick={() => deleteExperience(exp.id)}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </CardHeader>
                  <CardContent className="p-4 pt-1 space-y-2">
                    {exp.description && (
                      <p className="text-sm text-muted-foreground whitespace-pre-line">
                        {exp.description}
                      </p>
                    )}
                    {exp.achievements && exp.achievements.length > 0 && (
                      <ul className="list-disc list-inside text-xs space-y-1 text-muted-foreground">
                        {exp.achievements.map((ach, i) => (
                          <li key={i}>{ach}</li>
                        ))}
                      </ul>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        {/* 3. EDUCATION */}
        <TabsContent value="education" className="space-y-4">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-lg font-semibold">Education</h2>
              <p className="text-xs text-muted-foreground">Academic credentials, degrees, and institutions.</p>
            </div>
            <Button size="sm" onClick={() => setEduModalOpen(true)} className="gap-1">
              <Plus className="h-4 w-4" /> Add Education
            </Button>
          </div>

          {(!profile.educations || profile.educations.length === 0) ? (
            <EmptyState
              title="No education added"
              description="Add your degrees, universities, or academic qualifications."
            />
          ) : (
            <div className="space-y-3">
              {profile.educations.map((edu) => (
                <Card key={edu.id}>
                  <CardHeader className="p-4">
                    <div className="flex items-start justify-between">
                      <div>
                        <CardTitle className="text-base font-semibold">{edu.institution}</CardTitle>
                        <CardDescription className="text-sm text-foreground">
                          {edu.degree} {edu.field_of_study && `in ${edu.field_of_study}`}
                        </CardDescription>
                        {edu.gpa && (
                          <Badge variant="outline" className="mt-2 text-xs">
                            GPA: {edu.gpa}
                          </Badge>
                        )}
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-destructive h-8 w-8 p-0"
                        onClick={() => deleteEducation(edu.id)}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </CardHeader>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        {/* 4. SKILLS */}
        <TabsContent value="skills" className="space-y-4">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-lg font-semibold">Skills Inventory</h2>
              <p className="text-xs text-muted-foreground">
                Normalized skills distinguishing between user-verified and AI-inferred capabilities.
              </p>
            </div>
            <Button size="sm" onClick={() => setSkillModalOpen(true)} className="gap-1">
              <Plus className="h-4 w-4" /> Add Skill
            </Button>
          </div>

          {(!profile.skills || profile.skills.length === 0) ? (
            <EmptyState
              title="No skills recorded"
              description="Add technical skills, tools, and methodologies you are proficient with."
            />
          ) : (
            <div className="flex flex-wrap gap-2">
              {profile.skills.map((skill) => (
                <div
                  key={skill.id}
                  className="flex items-center gap-2 px-3 py-1.5 rounded-lg border bg-card text-sm"
                >
                  <span className="font-medium">{skill.name}</span>
                  <Badge
                    variant={skill.source === "USER_PROVIDED" ? "default" : "secondary"}
                    className="text-[10px] uppercase font-mono px-1 py-0"
                  >
                    {skill.source === "USER_PROVIDED" ? "Verified" : skill.source}
                  </Badge>
                  <button
                    type="button"
                    onClick={() => deleteSkill(skill.id)}
                    className="text-muted-foreground hover:text-destructive"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </TabsContent>

        {/* 5. PROJECTS */}
        <TabsContent value="projects" className="space-y-4">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-lg font-semibold">Projects & Key Work</h2>
              <p className="text-xs text-muted-foreground">
                Highlighted technical projects with explicit technologies and verifiable links.
              </p>
            </div>
            <Button size="sm" onClick={() => setProjModalOpen(true)} className="gap-1">
              <Plus className="h-4 w-4" /> Add Project
            </Button>
          </div>

          {(!profile.projects || profile.projects.length === 0) ? (
            <EmptyState
              title="No projects added"
              description="Showcase significant open-source, enterprise, or personal projects."
            />
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {profile.projects.map((proj) => (
                <Card key={proj.id}>
                  <CardHeader className="p-4 pb-2">
                    <div className="flex items-start justify-between">
                      <div>
                        <CardTitle className="text-base font-semibold">{proj.name}</CardTitle>
                        {proj.role && <CardDescription className="text-xs">{proj.role}</CardDescription>}
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-destructive h-8 w-8 p-0"
                        onClick={() => deleteProject(proj.id)}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </CardHeader>
                  <CardContent className="p-4 pt-1 space-y-2">
                    {proj.description && (
                      <p className="text-xs text-muted-foreground">{proj.description}</p>
                    )}
                    {proj.technologies && proj.technologies.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-2">
                        {proj.technologies.map((t, i) => (
                          <Badge key={i} variant="outline" className="text-[10px]">
                            {t}
                          </Badge>
                        ))}
                      </div>
                    )}
                    <div className="flex gap-3 pt-2 text-xs">
                      {proj.github_url && (
                        <a
                          href={proj.github_url}
                          target="_blank"
                          rel="noreferrer"
                          className="flex items-center gap-1 text-primary hover:underline"
                        >
                          <ExternalLink className="h-3 w-3" /> GitHub
                        </a>
                      )}
                      {proj.project_url && (
                        <a
                          href={proj.project_url}
                          target="_blank"
                          rel="noreferrer"
                          className="flex items-center gap-1 text-primary hover:underline"
                        >
                          <ExternalLink className="h-3 w-3" /> Live Demo
                        </a>
                      )}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        {/* 6. CERTIFICATIONS */}
        <TabsContent value="certifications" className="space-y-4">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-lg font-semibold">Certifications & Licenses</h2>
              <p className="text-xs text-muted-foreground">Industry-recognized professional certifications.</p>
            </div>
            <Button size="sm" onClick={() => setCertModalOpen(true)} className="gap-1">
              <Plus className="h-4 w-4" /> Add Certification
            </Button>
          </div>

          {(!profile.certifications || profile.certifications.length === 0) ? (
            <EmptyState
              title="No certifications added"
              description="Add certifications from AWS, GCP, Microsoft, or other accredited bodies."
            />
          ) : (
            <div className="space-y-3">
              {profile.certifications.map((cert) => (
                <Card key={cert.id}>
                  <CardHeader className="p-4">
                    <div className="flex items-start justify-between">
                      <div>
                        <CardTitle className="text-base font-semibold">{cert.name}</CardTitle>
                        <CardDescription className="text-xs">{cert.issuing_organization}</CardDescription>
                        {cert.credential_id && (
                          <div className="text-[11px] text-muted-foreground mt-1">
                            ID: {cert.credential_id}
                          </div>
                        )}
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-destructive h-8 w-8 p-0"
                        onClick={() => deleteCertification(cert.id)}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </CardHeader>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>

      {/* MODAL: ADD EDUCATION */}
      <Dialog open={eduModalOpen} onOpenChange={setEduModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add Education</DialogTitle>
            <DialogDescription>Record degree, field of study, and institution.</DialogDescription>
          </DialogHeader>
          <form onSubmit={handleAddEducation} className="space-y-3">
            <div className="space-y-1">
              <label className="text-xs font-medium">Institution *</label>
              <Input
                placeholder="e.g. University of Waterloo"
                value={eduForm.institution}
                onChange={(e) => setEduForm({ ...eduForm, institution: e.target.value })}
                required
              />
            </div>
            <div className="grid grid-cols-2 gap-2">
              <div className="space-y-1">
                <label className="text-xs font-medium">Degree</label>
                <Input
                  placeholder="e.g. B.S."
                  value={eduForm.degree || ""}
                  onChange={(e) => setEduForm({ ...eduForm, degree: e.target.value })}
                />
              </div>
              <div className="space-y-1">
                <label className="text-xs font-medium">Field of Study</label>
                <Input
                  placeholder="e.g. Computer Engineering"
                  value={eduForm.field_of_study || ""}
                  onChange={(e) => setEduForm({ ...eduForm, field_of_study: e.target.value })}
                />
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setEduModalOpen(false)}>
                Cancel
              </Button>
              <Button type="submit">Add Record</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* MODAL: ADD EXPERIENCE */}
      <Dialog open={expModalOpen} onOpenChange={setExpModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add Work Experience</DialogTitle>
            <DialogDescription>Record role, company, and explicit responsibilities.</DialogDescription>
          </DialogHeader>
          <form onSubmit={handleAddExperience} className="space-y-3">
            <div className="grid grid-cols-2 gap-2">
              <div className="space-y-1">
                <label className="text-xs font-medium">Company *</label>
                <Input
                  placeholder="e.g. Stripe"
                  value={expForm.company}
                  onChange={(e) => setExpForm({ ...expForm, company: e.target.value })}
                  required
                />
              </div>
              <div className="space-y-1">
                <label className="text-xs font-medium">Job Title *</label>
                <Input
                  placeholder="e.g. Backend Engineer"
                  value={expForm.title}
                  onChange={(e) => setExpForm({ ...expForm, title: e.target.value })}
                  required
                />
              </div>
            </div>
            <div className="space-y-1">
              <label className="text-xs font-medium">Description</label>
              <Textarea
                rows={3}
                placeholder="Core responsibilities and scope of work..."
                value={expForm.description || ""}
                onChange={(e) => setExpForm({ ...expForm, description: e.target.value })}
              />
            </div>
            <div className="space-y-1">
              <label className="text-xs font-medium">Key Achievements (one per line)</label>
              <Textarea
                rows={3}
                placeholder="Increased throughput by 30%...&#10;Architected multi-tenant Postgres cluster..."
                value={achievementsText}
                onChange={(e) => setAchievementsText(e.target.value)}
              />
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setExpModalOpen(false)}>
                Cancel
              </Button>
              <Button type="submit">Add Experience</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* MODAL: ADD SKILL */}
      <Dialog open={skillModalOpen} onOpenChange={setSkillModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add Skill</DialogTitle>
            <DialogDescription>Specify normalized skill name and category.</DialogDescription>
          </DialogHeader>
          <form onSubmit={handleAddSkill} className="space-y-3">
            <div className="space-y-1">
              <label className="text-xs font-medium">Skill Name *</label>
              <Input
                placeholder="e.g. Python, Docker, PostgreSQL"
                value={skillForm.name}
                onChange={(e) => setSkillForm({ ...skillForm, name: e.target.value })}
                required
              />
            </div>
            <div className="grid grid-cols-2 gap-2">
              <div className="space-y-1">
                <label className="text-xs font-medium">Category</label>
                <Input
                  placeholder="e.g. Backend, Frontend, DevOps"
                  value={skillForm.category || ""}
                  onChange={(e) => setSkillForm({ ...skillForm, category: e.target.value })}
                />
              </div>
              <div className="space-y-1">
                <label className="text-xs font-medium">Years of Experience</label>
                <Input
                  type="number"
                  step="0.5"
                  placeholder="e.g. 4"
                  value={skillForm.years_of_experience ?? ""}
                  onChange={(e) =>
                    setSkillForm({
                      ...skillForm,
                      years_of_experience: e.target.value ? parseFloat(e.target.value) : undefined,
                    })
                  }
                />
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setSkillModalOpen(false)}>
                Cancel
              </Button>
              <Button type="submit">Add Skill</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* MODAL: ADD PROJECT */}
      <Dialog open={projModalOpen} onOpenChange={setProjModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add Project</DialogTitle>
            <DialogDescription>Record a project and its technological stack.</DialogDescription>
          </DialogHeader>
          <form onSubmit={handleAddProject} className="space-y-3">
            <div className="grid grid-cols-2 gap-2">
              <div className="space-y-1">
                <label className="text-xs font-medium">Project Name *</label>
                <Input
                  placeholder="e.g. ResumeForge"
                  value={projForm.name}
                  onChange={(e) => setProjForm({ ...projForm, name: e.target.value })}
                  required
                />
              </div>
              <div className="space-y-1">
                <label className="text-xs font-medium">Role</label>
                <Input
                  placeholder="e.g. Lead Developer"
                  value={projForm.role || ""}
                  onChange={(e) => setProjForm({ ...projForm, role: e.target.value })}
                />
              </div>
            </div>
            <div className="space-y-1">
              <label className="text-xs font-medium">Description</label>
              <Textarea
                rows={2}
                placeholder="Overview of project objectives and architecture..."
                value={projForm.description || ""}
                onChange={(e) => setProjForm({ ...projForm, description: e.target.value })}
              />
            </div>
            <div className="space-y-1">
              <label className="text-xs font-medium">Technologies (comma separated)</label>
              <Input
                placeholder="Python, Next.js, Redis, PostgreSQL"
                value={techText}
                onChange={(e) => setTechText(e.target.value)}
              />
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setProjModalOpen(false)}>
                Cancel
              </Button>
              <Button type="submit">Add Project</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* MODAL: ADD CERTIFICATION */}
      <Dialog open={certModalOpen} onOpenChange={setCertModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add Certification</DialogTitle>
            <DialogDescription>Record accredited credential.</DialogDescription>
          </DialogHeader>
          <form onSubmit={handleAddCertification} className="space-y-3">
            <div className="space-y-1">
              <label className="text-xs font-medium">Certification Name *</label>
              <Input
                placeholder="e.g. AWS Certified Solutions Architect"
                value={certForm.name}
                onChange={(e) => setCertForm({ ...certForm, name: e.target.value })}
                required
              />
            </div>
            <div className="space-y-1">
              <label className="text-xs font-medium">Issuing Organization</label>
              <Input
                placeholder="e.g. Amazon Web Services"
                value={certForm.issuing_organization || ""}
                onChange={(e) => setCertForm({ ...certForm, issuing_organization: e.target.value })}
              />
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setCertModalOpen(false)}>
                Cancel
              </Button>
              <Button type="submit">Add Certification</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
