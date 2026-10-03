import type { Metadata } from "next";
import { Shell } from "@/components/layout/shell";

export const metadata: Metadata = {
  title: {
    default: "Dashboard",
    template: "%s | ResumeForge",
  },
};

interface DashboardLayoutProps {
  children: React.ReactNode;
}

export default function DashboardLayout({ children }: DashboardLayoutProps) {
  return <Shell>{children}</Shell>;
}
