import { clsx } from "clsx";
import type { ButtonHTMLAttributes } from "react";

interface Props extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "ghost" | "danger" | "outline";
  size?: "sm" | "md" | "lg";
  loading?: boolean;
}

export default function Button({
  variant = "primary",
  size = "md",
  loading,
  disabled,
  className,
  children,
  ...rest
}: Props) {
  return (
    <button
      disabled={disabled || loading}
      className={clsx(
        "inline-flex items-center justify-center gap-2 rounded-lg font-semibold transition-all focus:outline-none focus:ring-2 focus:ring-nexus-cyan/50 disabled:opacity-50 disabled:cursor-not-allowed",
        {
          "bg-nexus-cyan text-black hover:bg-cyan-300 focus:ring-nexus-cyan": variant === "primary",
          "border border-nexus-border text-gray-300 hover:border-nexus-cyan hover:text-nexus-cyan bg-transparent": variant === "outline",
          "text-gray-400 hover:text-white bg-transparent hover:bg-white/5": variant === "ghost",
          "bg-red-600 text-white hover:bg-red-500": variant === "danger",
          "px-3 py-1.5 text-xs": size === "sm",
          "px-4 py-2 text-sm": size === "md",
          "px-6 py-3 text-base": size === "lg",
        },
        className
      )}
      {...rest}
    >
      {loading && (
        <span className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
      )}
      {children}
    </button>
  );
}
