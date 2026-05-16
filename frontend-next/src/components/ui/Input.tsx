import { clsx } from "clsx";
import type { InputHTMLAttributes, TextareaHTMLAttributes } from "react";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

export function Input({ label, error, className, ...rest }: InputProps) {
  return (
    <div className="flex flex-col gap-1">
      {label && <label className="text-xs font-semibold text-gray-400 uppercase tracking-wider">{label}</label>}
      <input
        className={clsx(
          "w-full px-3 py-2 rounded-lg bg-white/5 border text-sm text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-nexus-cyan/50 transition-colors",
          error ? "border-red-500" : "border-nexus-border hover:border-gray-600",
          className
        )}
        {...rest}
      />
      {error && <p className="text-xs text-red-400">{error}</p>}
    </div>
  );
}

interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
}

export function Textarea({ label, error, className, ...rest }: TextareaProps) {
  return (
    <div className="flex flex-col gap-1">
      {label && <label className="text-xs font-semibold text-gray-400 uppercase tracking-wider">{label}</label>}
      <textarea
        className={clsx(
          "w-full px-3 py-2 rounded-lg bg-white/5 border text-sm text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-nexus-cyan/50 transition-colors resize-none",
          error ? "border-red-500" : "border-nexus-border hover:border-gray-600",
          className
        )}
        {...rest}
      />
      {error && <p className="text-xs text-red-400">{error}</p>}
    </div>
  );
}
