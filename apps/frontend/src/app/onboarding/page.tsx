"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { profileApi } from "@/lib/api/profile";
import { resumesApi } from "@/lib/api/resumes";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";

export default function OnboardingPage() {
  const router = useRouter();
  const { user, completeOnboarding } = useAuth();
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);

  // Step 1: Basic Info
  const [fullName, setFullName] = useState(user?.full_name || "");
  const [targetRole, setTargetRole] = useState("Software Engineer");
  const [location, setLocation] = useState("");
  const [phone, setPhone] = useState("");
  const [summary, setSummary] = useState("");

  // Step 2: Education
  const [institution, setInstitution] = useState("");
  const [degree, setDegree] = useState("");
  const [fieldOfStudy, setFieldOfStudy] = useState("");
  const [gradYear, setGradYear] = useState("");

  // Step 3: Skills
  const [skillInput, setSkillInput] = useState("");
  const [skills, setSkills] = useState<string[]>([
    "Python", "JavaScript", "TypeScript", "React", "PostgreSQL", "Git"
  ]);

  // Step 4: Experience / Project
  const [expTitle, setExpTitle] = useState("");
  const [company, setCompany] = useState("");
  const [expDescription, setExpDescription] = useState("");

  // Step 5: Resume
  const [resumeTitle, setResumeTitle] = useState("My Master Resume");

  const totalSteps = 5;

  const handleAddSkill = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && skillInput.trim()) {
      e.preventDefault();
      if (!skills.includes(skillInput.trim())) {
        setSkills([...skills, skillInput.trim()]);
      }
      setSkillInput("");
    }
  };

  const handleRemoveSkill = (skillToRemove: string) => {
    setSkills(skills.filter((s) => s !== skillToRemove));
  };

  const handleNext = async () => {
    setLoading(true);
    try {
      if (step === 1) {
        await profileApi.updateProfile({
          full_name: fullName || user?.full_name || "Candidate User",
          headline: targetRole,
          summary: summary || undefined,
          location: location || undefined,
          phone: phone || undefined,
          preferred_roles: targetRole ? [targetRole] : [],
        });
      } else if (step === 2 && institution && degree) {
        await profileApi.addEducation({
          institution,
          degree,
          field_of_study: fieldOfStudy || undefined,
          start_date: "2020-09-01",
          end_date: gradYear ? `${gradYear}-05-01` : undefined,
          is_current: false,
        });
      } else if (step === 3 && skills.length > 0) {
        for (const sk of skills.slice(0, 10)) {
          try {
            await profileApi.addSkill({
              name: sk,
              category: "TECHNICAL",
              proficiency: "INTERMEDIATE",
              source: "USER_PROVIDED",
            });
          } catch {
            // Ignore duplicates
          }
        }
      } else if (step === 4 && expTitle && company) {
        await profileApi.addExperience({
          title: expTitle,
          company,
          location: location || undefined,
          start_date: "2022-01-01",
          is_current: true,
          description: expDescription || undefined,
          achievements: [],
        });
      } else if (step === 5) {
        // Create initial master resume
        try {
          await resumesApi.createResume({
            title: resumeTitle || "Master Resume",
            target_role: targetRole || "General",
          });
        } catch {
          // Ignore
        }
        await completeOnboarding();
        return;
      }

      if (step < totalSteps) {
        setStep(step + 1);
      } else {
        await completeOnboarding();
      }
    } catch (err) {
      console.error("Step save error:", err);
      if (step < totalSteps) {
        setStep(step + 1);
      } else {
        await completeOnboarding();
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSkip = () => {
    if (step < totalSteps) {
      setStep(step + 1);
    } else {
      completeOnboarding();
    }
  };

  return (
    <div className="flex min-h-screen flex-col bg-slate-50 dark:bg-slate-950 p-4 sm:p-6 lg:p-8">
      {/* Top Header */}
      <header className="mx-auto w-full max-w-2xl flex items-center justify-between pb-6">
        <Link href="/" className="inline-flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-600 text-white font-bold text-xs">
            RF
          </div>
          <span className="font-bold text-lg">ResumeForge</span>
        </Link>
        <button
          onClick={() => completeOnboarding()}
          className="text-xs text-slate-500 hover:text-slate-800 dark:hover:text-slate-200 underline"
        >
          Skip onboarding completely
        </button>
      </header>

      {/* Main wizard card */}
      <main className="mx-auto w-full max-w-2xl flex-1 flex flex-col justify-center">
        <Card className="border-slate-200 dark:border-slate-800 shadow-sm">
          {/* Progress bar header */}
          <div className="p-6 border-b border-slate-100 dark:border-slate-800">
            <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400 mb-2">
              <span className="font-semibold text-blue-600 uppercase tracking-wider">
                Step {step} of {totalSteps}
              </span>
              <span>{Math.round((step / totalSteps) * 100)}% complete</span>
            </div>
            <div className="h-1.5 w-full rounded-full bg-slate-100 dark:bg-slate-800 overflow-hidden">
              <div
                className="h-full bg-blue-600 transition-all duration-300 rounded-full"
                style={{ width: `${(step / totalSteps) * 100}%` }}
              />
            </div>
          </div>

          <CardHeader className="pt-6">
            {step === 1 && (
              <>
                <CardTitle className="text-xl">Let&apos;s start with your basics</CardTitle>
                <CardDescription>
                  This forms the header of your Master Career Profile.
                </CardDescription>
              </>
            )}
            {step === 2 && (
              <>
                <CardTitle className="text-xl">Where did you study?</CardTitle>
                <CardDescription>
                  Add your highest degree or college education.
                </CardDescription>
              </>
            )}
            {step === 3 && (
              <>
                <CardTitle className="text-xl">What are your top skills?</CardTitle>
                <CardDescription>
                  ResumeForge uses your skills to match against job descriptions.
                </CardDescription>
              </>
            )}
            {step === 4 && (
              <>
                <CardTitle className="text-xl">Add a recent role or project</CardTitle>
                <CardDescription>
                  Demonstrates your real experience for Truth Guard evidence.
                </CardDescription>
              </>
            )}
            {step === 5 && (
              <>
                <CardTitle className="text-xl">Create your initial resume</CardTitle>
                <CardDescription>
                  Give your master resume a name to begin tailoring.
                </CardDescription>
              </>
            )}
          </CardHeader>

          <CardContent className="space-y-4">
            {/* STEP 1 */}
            {step === 1 && (
              <div className="space-y-4">
                <div>
                  <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                    Full Name
                  </label>
                  <input
                    type="text"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    placeholder="Jane Candidate"
                    className="mt-1 w-full h-10 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 px-3 text-sm focus:ring-2 focus:ring-blue-600"
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                    Target Job Title / Career Goal
                  </label>
                  <input
                    type="text"
                    value={targetRole}
                    onChange={(e) => setTargetRole(e.target.value)}
                    placeholder="Full Stack Developer, Data Analyst, Product Manager..."
                    className="mt-1 w-full h-10 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 px-3 text-sm focus:ring-2 focus:ring-blue-600"
                  />
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                      Location
                    </label>
                    <input
                      type="text"
                      value={location}
                      onChange={(e) => setLocation(e.target.value)}
                      placeholder="San Francisco, CA or Remote"
                      className="mt-1 w-full h-10 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 px-3 text-sm focus:ring-2 focus:ring-blue-600"
                    />
                  </div>
                  <div>
                    <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                      Phone Number (Optional)
                    </label>
                    <input
                      type="text"
                      value={phone}
                      onChange={(e) => setPhone(e.target.value)}
                      placeholder="+1 (555) 012-3456"
                      className="mt-1 w-full h-10 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 px-3 text-sm focus:ring-2 focus:ring-blue-600"
                    />
                  </div>
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                    Brief Professional Summary
                  </label>
                  <textarea
                    rows={3}
                    value={summary}
                    onChange={(e) => setSummary(e.target.value)}
                    placeholder="Passionate engineer with experience in React, Python, and scalable web apps..."
                    className="mt-1 w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 p-3 text-sm focus:ring-2 focus:ring-blue-600"
                  />
                </div>
              </div>
            )}

            {/* STEP 2 */}
            {step === 2 && (
              <div className="space-y-4">
                <div>
                  <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                    School / University
                  </label>
                  <input
                    type="text"
                    value={institution}
                    onChange={(e) => setInstitution(e.target.value)}
                    placeholder="University of California, Berkeley"
                    className="mt-1 w-full h-10 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 px-3 text-sm focus:ring-2 focus:ring-blue-600"
                  />
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                      Degree
                    </label>
                    <input
                      type="text"
                      value={degree}
                      onChange={(e) => setDegree(e.target.value)}
                      placeholder="Bachelor of Science"
                      className="mt-1 w-full h-10 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 px-3 text-sm focus:ring-2 focus:ring-blue-600"
                    />
                  </div>
                  <div>
                    <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                      Field of Study
                    </label>
                    <input
                      type="text"
                      value={fieldOfStudy}
                      onChange={(e) => setFieldOfStudy(e.target.value)}
                      placeholder="Computer Science"
                      className="mt-1 w-full h-10 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 px-3 text-sm focus:ring-2 focus:ring-blue-600"
                    />
                  </div>
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                    Graduation Year
                  </label>
                  <input
                    type="text"
                    value={gradYear}
                    onChange={(e) => setGradYear(e.target.value)}
                    placeholder="2024"
                    className="mt-1 w-full h-10 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 px-3 text-sm focus:ring-2 focus:ring-blue-600"
                  />
                </div>
              </div>
            )}

            {/* STEP 3 */}
            {step === 3 && (
              <div className="space-y-4">
                <div>
                  <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                    Add Skills (type and press Enter)
                  </label>
                  <input
                    type="text"
                    value={skillInput}
                    onChange={(e) => setSkillInput(e.target.value)}
                    onKeyDown={handleAddSkill}
                    placeholder="e.g. Next.js, Docker, SQL, Machine Learning..."
                    className="mt-1 w-full h-10 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 px-3 text-sm focus:ring-2 focus:ring-blue-600"
                  />
                </div>
                <div className="flex flex-wrap gap-2 pt-2">
                  {skills.map((skill) => (
                    <span
                      key={skill}
                      className="inline-flex items-center gap-1.5 rounded-full bg-blue-50 dark:bg-blue-950/60 border border-blue-200 dark:border-blue-900 px-3 py-1 text-xs font-medium text-blue-700 dark:text-blue-300"
                    >
                      {skill}
                      <button
                        type="button"
                        onClick={() => handleRemoveSkill(skill)}
                        className="text-blue-400 hover:text-blue-600"
                      >
                        ×
                      </button>
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* STEP 4 */}
            {step === 4 && (
              <div className="space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                      Role / Project Title
                    </label>
                    <input
                      type="text"
                      value={expTitle}
                      onChange={(e) => setExpTitle(e.target.value)}
                      placeholder="Software Engineering Intern"
                      className="mt-1 w-full h-10 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 px-3 text-sm focus:ring-2 focus:ring-blue-600"
                    />
                  </div>
                  <div>
                    <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                      Company / Organization
                    </label>
                    <input
                      type="text"
                      value={company}
                      onChange={(e) => setCompany(e.target.value)}
                      placeholder="Acme Tech"
                      className="mt-1 w-full h-10 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 px-3 text-sm focus:ring-2 focus:ring-blue-600"
                    />
                  </div>
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                    What did you build or achieve?
                  </label>
                  <textarea
                    rows={3}
                    value={expDescription}
                    onChange={(e) => setExpDescription(e.target.value)}
                    placeholder="Designed and built a REST API backend with automated tests, reducing load time by 30%..."
                    className="mt-1 w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 p-3 text-sm focus:ring-2 focus:ring-blue-600"
                  />
                </div>
              </div>
            )}

            {/* STEP 5 */}
            {step === 5 && (
              <div className="space-y-4">
                <div>
                  <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                    Resume Title
                  </label>
                  <input
                    type="text"
                    value={resumeTitle}
                    onChange={(e) => setResumeTitle(e.target.value)}
                    placeholder="My Master Resume"
                    className="mt-1 w-full h-10 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 px-3 text-sm focus:ring-2 focus:ring-blue-600"
                  />
                </div>
                <div className="rounded-xl border border-dashed border-slate-300 dark:border-slate-700 p-6 text-center">
                  <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-blue-50 dark:bg-blue-950 text-blue-600 text-xl mb-3">
                    📄
                  </div>
                  <h4 className="text-sm font-semibold">Your Master Resume is Ready to Seed</h4>
                  <p className="mt-1 text-xs text-slate-500 max-w-sm mx-auto">
                    ResumeForge will compile your education, skills, and experiences into version 1.0. You can upload existing PDFs or DOCX files anytime!
                  </p>
                </div>
              </div>
            )}
          </CardContent>

          <CardFooter className="flex items-center justify-between border-t border-slate-100 dark:border-slate-800 pt-4">
            <Button
              type="button"
              variant="ghost"
              onClick={handleSkip}
              disabled={loading}
              className="text-xs text-slate-500"
            >
              Skip this step
            </Button>
            <Button
              type="button"
              onClick={handleNext}
              disabled={loading}
              className="bg-blue-600 hover:bg-blue-700 text-white font-medium"
            >
              {loading
                ? "Saving..."
                : step === totalSteps
                ? "Complete Setup & Open Dashboard"
                : "Save & Continue"}
            </Button>
          </CardFooter>
        </Card>
      </main>
    </div>
  );
}
