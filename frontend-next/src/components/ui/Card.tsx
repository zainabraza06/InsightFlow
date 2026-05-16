import { clsx } from "clsx";
import type { HTMLAttributes } from "react";

interface Props extends HTMLAttributes<HTMLDivElement> {
  glow?: "cyan" | "purple" | "green" | "amber" | "red";
}

export default function Card({ glow, className, children, ...rest }: Props) {
  return (
    <div
      className={clsx(
        "rounded-xl border bg-nexus-card",
        {
          "border-nexus-border": !glow,
          "border-nexus-cyan/30 shadow-[0_0_20px_rgba(0,212,255,0.08)]": glow === "cyan",
          "border-nexus-purple/30 shadow-[0_0_20px_rgba(155,89,182,0.08)]": glow === "purple",
          "border-nexus-green/30 shadow-[0_0_20px_rgba(0,255,136,0.08)]": glow === "green",
          "border-nexus-amber/30 shadow-[0_0_20px_rgba(245,158,11,0.08)]": glow === "amber",
          "border-nexus-red/30 shadow-[0_0_20px_rgba(239,68,68,0.08)]": glow === "red",
        },
        className
      )}
      {...rest}
    >
      {children}
    </div>
  );
}
