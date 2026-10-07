"use client";

import React, { useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { Button } from "@/components/ui/button";

export default function WelcomePage() {
  const router = useRouter();
  const { isAuthenticated, user, isLoading } = useAuth();

  useEffect(() => {
    if (!isLoading && isAuthenticated && user) {
      if (!user.onboarding_completed) {
        router.push("/onboarding");
      } else {
        router.push("/dashboard");
      }
    }
  }, [isLoading, isAuthenticated, user, router]);

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50 dark:bg-slate-950">
        <div className="flex flex-col items-center gap-3">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent" />
          <p className="text-sm font-medium text-slate-500">Loading ResumeForge...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen flex-col bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 selection:bg-blue-100 selection:text-blue-900">
      {/* Top Navbar */}
      <header className="sticky top-0 z-30 border-b border-slate-200/80 dark:border-slate-800/80 bg-white/80 dark:bg-slate-900/80 backdrop-blur-md">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
          <Link href="/" className="inline-flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-blue-600 text-white font-bold text-sm shadow-sm">
              RF
            </div>
            <span className="text-xl font-bold tracking-tight">
              Resume<span className="text-blue-600">Forge</span>
            </span>
          </Link>
          <div className="flex items-center gap-3">
            <Link href="/login">
              <Button variant="ghost" className="text-sm font-medium">
                Sign in
              </Button>
            </Link>
            <Link href="/register">
              <Button className="bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium shadow-sm">
                Get started
              </Button>
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <main className="flex-1">
        <section className="relative overflow-hidden py-20 sm:py-28">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 text-center">
            <div className="inline-flex items-center gap-2 rounded-full border border-blue-200 dark:border-blue-900/60 bg-blue-50/80 dark:bg-blue-950/40 px-3.5 py-1 text-xs font-semibold text-blue-700 dark:text-blue-400 mb-8 shadow-sm">
              <span className="inline-block h-2 w-2 rounded-full bg-blue-600 animate-pulse" />
              Truth Guard 2.0 • Zero Hallucination Guarantee
            </div>
            <h1 className="mx-auto max-w-4xl text-4xl font-extrabold tracking-tight sm:text-6xl sm:leading-tight">
              Land your next role with{" "}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-indigo-600">
                precision resume engineering
              </span>
            </h1>
            <p className="mx-auto mt-6 max-w-2xl text-lg text-slate-600 dark:text-slate-400 leading-relaxed">
              Stop guessing why your resume gets rejected. ResumeForge analyzes job descriptions,
              scores your real profile evidence, and tailors every bullet point without fabricating claims.
            </p>

            <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link href="/register" className="w-full sm:w-auto">
                <Button className="w-full sm:w-auto h-12 px-8 bg-blue-600 hover:bg-blue-700 text-white text-base font-medium rounded-xl shadow-md hover:shadow-lg transition-all">
                  I&apos;m New Here — Create Free Account
                </Button>
              </Link>
              <Link href="/login" className="w-full sm:w-auto">
                <Button variant="outline" className="w-full sm:w-auto h-12 px-8 text-base font-medium rounded-xl border-slate-300 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800">
                  Already Have an Account — Sign In
                </Button>
              </Link>
            </div>

            {/* Feature Highlights Grid */}
            <div className="mx-auto mt-20 max-w-5xl grid grid-cols-1 md:grid-cols-3 gap-8 text-left">
              <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 shadow-sm">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-emerald-100 dark:bg-emerald-950 text-emerald-600 dark:text-emerald-400 font-bold mb-4">
                  🎯
                </div>
                <h3 className="text-lg font-semibold mb-2">Instant Fit Breakdown</h3>
                <p className="text-sm text-slate-600 dark:text-slate-400 leading-relaxed">
                  Clear, human-readable match percentages. Know immediately what required skills you have, what you should highlight, and what is missing.
                </p>
              </div>

              <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 shadow-sm">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-100 dark:bg-blue-950 text-blue-600 dark:text-blue-400 font-bold mb-4">
                  🛡️
                </div>
                <h3 className="text-lg font-semibold mb-2">Truth Guard Verification</h3>
                <p className="text-sm text-slate-600 dark:text-slate-400 leading-relaxed">
                  Never get caught in an interview for skills you do not have. Every AI tailoring suggestion is strictly audited against your master profile truth.
                </p>
              </div>

              <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 shadow-sm">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-indigo-100 dark:bg-indigo-950 text-indigo-600 dark:text-indigo-400 font-bold mb-4">
                  📊
                </div>
                <h3 className="text-lg font-semibold mb-2">Track & Optimize</h3>
                <p className="text-sm text-slate-600 dark:text-slate-400 leading-relaxed">
                  Log your applications, compare version diffs, and inspect before/after match score jumps for every single position you apply to.
                </p>
              </div>
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 py-8">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 text-center text-xs text-slate-500">
          © {new Date().getFullYear()} ResumeForge. Built for ambitious candidates and career changers.
        </div>
      </footer>
    </div>
  );
}
