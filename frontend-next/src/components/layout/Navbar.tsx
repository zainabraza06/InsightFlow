"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { clearAuth, getUser } from "@/lib/auth";
import Button from "@/components/ui/Button";

interface Props {
  metrics?: {
    sources?: number;
    trusted?: number;
    contradictions?: number;
    actions?: number;
    cost?: number;
  };
}

export default function Navbar({ metrics }: Props) {
  const router = useRouter();
  const user = getUser();

  function logout() {
    clearAuth();
    router.push("/login");
  }

  return (
    <header className="h-14 border-b border-nexus-border bg-nexus-card/80 backdrop-blur flex items-center px-6 gap-4 shrink-0">
      {metrics && (
        <div className="flex items-center gap-4 text-xs font-mono flex-1">
          {metrics.sources !== undefined && (
            <span className="text-gray-500">
              Sources: <span className="text-nexus-cyan">{metrics.sources}</span>
            </span>
          )}
          {metrics.trusted !== undefined && (
            <span className="text-gray-500">
              Trusted: <span className="text-nexus-green">{metrics.trusted}</span>
            </span>
          )}
          {metrics.contradictions !== undefined && (
            <span className="text-gray-500">
              Contradictions: <span className="text-nexus-amber">{metrics.contradictions}</span>
            </span>
          )}
          {metrics.actions !== undefined && (
            <span className="text-gray-500">
              Actions: <span className="text-nexus-purple">{metrics.actions}</span>
            </span>
          )}
          {metrics.cost !== undefined && (
            <span className="text-gray-500">
              Cost: <span className="text-white">PKR {metrics.cost.toLocaleString()}</span>
            </span>
          )}
        </div>
      )}
      <div className="ml-auto flex items-center gap-3">
        {user && (
          <span className="text-sm text-gray-400">
            {user.name}
          </span>
        )}
        <Link href="/settings">
          <Button variant="ghost" size="sm">Profile</Button>
        </Link>
        <Button variant="outline" size="sm" onClick={logout}>
          Logout
        </Button>
      </div>
    </header>
  );
}
