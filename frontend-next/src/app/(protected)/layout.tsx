"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { isAuthenticated, clearAuth, getToken } from "@/lib/auth";
import Sidebar from "@/components/layout/Sidebar";
import { FullPageLoader } from "@/components/ui/LoadingSpinner";

export default function ProtectedLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace("/login");
      return;
    }
    // Check JWT expiry client-side without verifying signature
    try {
      const token = getToken()!;
      const payload = JSON.parse(atob(token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/")));
      if (payload.exp && payload.exp < Date.now() / 1000) {
        clearAuth();
        router.replace("/login");
        return;
      }
    } catch {
      // non-JWT token (base64 fallback) — let the server decide
    }
    setChecking(false);
  }, [router]);

  if (checking) return <FullPageLoader />;

  return (
    <div className="flex min-h-screen bg-nexus-bg">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {children}
      </div>
    </div>
  );
}
