"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { clsx } from "clsx";
import { getUser } from "@/lib/auth";

export default function Sidebar() {
  const pathname = usePathname();
  const user = getUser();
  const isAdmin = user?.is_admin === true;

  const navItems = [
    { href: "/dashboard", label: "Dashboard", icon: "⚡" },
    { href: "/analyze", label: "New Analysis", icon: "🔬" },
    { href: "/history", label: "History", icon: "📋" },
    { href: "/trace", label: "Trace Viewer", icon: "🛸" },
    { href: "/settings", label: "Settings", icon: "⚙️" },
  ];

  if (isAdmin) {
    navItems.push({ href: "/admin", label: "Admin Panel", icon: "🛡️" });
  }

  return (
    <aside className="w-56 shrink-0 flex flex-col border-r border-nexus-border bg-nexus-card min-h-screen">
      <div className="px-4 py-5 border-b border-nexus-border">
        <span className="font-mono font-bold text-nexus-cyan text-lg tracking-widest">InsightFlow</span>
        <p className="text-[10px] text-gray-500 mt-0.5">Autonomous Intelligence</p>
      </div>
      <nav className="flex-1 py-4 flex flex-col gap-1 px-2">
        {navItems.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={clsx(
              "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all",
              pathname === item.href
                ? "bg-nexus-cyan/10 text-nexus-cyan border border-nexus-cyan/20 font-semibold"
                : "text-gray-400 hover:text-white hover:bg-white/5"
            )}
          >
            <span className="text-base w-5 text-center">{item.icon}</span>
            {item.label}
          </Link>
        ))}
      </nav>
      <div className="px-4 py-4 border-t border-nexus-border">
        <p className="text-[10px] text-gray-600 font-mono">v2.0 · Autonomous Intelligence</p>
      </div>
    </aside>
  );
}
