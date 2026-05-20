import { clsx } from "clsx";

export default function LoadingSpinner({ className, size = "md" }: { className?: string; size?: "sm" | "md" | "lg" }) {
  return (
    <span
      className={clsx(
        "inline-block rounded-full border-2 border-nexus-cyan border-t-transparent animate-spin",
        { "w-4 h-4": size === "sm", "w-6 h-6": size === "md", "w-10 h-10": size === "lg" },
        className
      )}
    />
  );
}

export function FullPageLoader() {
  return (
    <div className="fixed inset-0 bg-nexus-bg flex items-center justify-center z-50">
      <div className="flex flex-col items-center gap-4">
        <LoadingSpinner size="lg" />
        <p className="text-nexus-cyan font-mono text-sm animate-pulse">InsightFlow initializing...</p>
      </div>
    </div>
  );
}
