import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "InsightFlow — Autonomous Intelligence Engine",
  description: "Autonomous Content-to-Action Agent with 5-agent consensus, contradiction detection, and real-world integrations.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-nexus-bg text-slate-200 antialiased">
        {children}
      </body>
    </html>
  );
}
