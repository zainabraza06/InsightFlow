import { clsx } from "clsx";

interface Props {
  variant?: "cyan" | "purple" | "green" | "amber" | "red" | "gray";
  children: React.ReactNode;
  className?: string;
}

export default function Badge({ variant = "gray", children, className }: Props) {
  return (
    <span
      className={clsx(
        "inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold",
        {
          "bg-nexus-cyan/10 text-nexus-cyan border border-nexus-cyan/30": variant === "cyan",
          "bg-nexus-purple/10 text-nexus-purple border border-nexus-purple/30": variant === "purple",
          "bg-nexus-green/10 text-nexus-green border border-nexus-green/30": variant === "green",
          "bg-nexus-amber/10 text-nexus-amber border border-nexus-amber/30": variant === "amber",
          "bg-nexus-red/10 text-nexus-red border border-nexus-red/30": variant === "red",
          "bg-white/5 text-gray-400 border border-white/10": variant === "gray",
        },
        className
      )}
    >
      {children}
    </span>
  );
}
