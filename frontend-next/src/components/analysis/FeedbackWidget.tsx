"use client";
import { useState } from "react";
import { clsx } from "clsx";
import Card from "@/components/ui/Card";
import Button from "@/components/ui/Button";

interface Props {
  domain: string;
  analysisId?: string;
  agentConfidences?: Record<string, number>;
  onSubmitted?: (rating: number) => void;
}

const RATINGS = [
  { value: 1, emoji: "😤", label: "Frustrated", color: "text-red-400 hover:bg-red-500/10 border-red-500/30" },
  { value: 2, emoji: "😞", label: "Disappointed", color: "text-orange-400 hover:bg-orange-500/10 border-orange-500/30" },
  { value: 3, emoji: "😐", label: "Okay", color: "text-gray-400 hover:bg-gray-500/10 border-gray-500/30" },
  { value: 4, emoji: "😊", label: "Satisfied", color: "text-nexus-cyan hover:bg-nexus-cyan/10 border-nexus-cyan/30" },
  { value: 5, emoji: "🤩", label: "Impressed", color: "text-nexus-green hover:bg-nexus-green/10 border-nexus-green/30" },
];

export default function FeedbackWidget({ domain, analysisId = "", agentConfidences, onSubmitted }: Props) {
  const [selected, setSelected] = useState<number | null>(null);
  const [comment, setComment] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [learningContext, setLearningContext] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState("");

  async function handleSubmit() {
    if (selected === null) return;
    setSubmitting(true);
    setError("");
    try {
      const token = typeof window !== "undefined" ? localStorage.getItem("nexus_token") : null;
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/feedback`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
          },
          body: JSON.stringify({
            rating: selected,
            domain,
            comment,
            analysis_id: analysisId,
            agent_confidences: agentConfidences,
          }),
        }
      );
      const data = await res.json();
      setLearningContext(data.learning_context);
      setSubmitted(true);
      onSubmitted?.(selected);
    } catch {
      setError("Failed to submit feedback");
    } finally {
      setSubmitting(false);
    }
  }

  if (submitted) {
    const avg = learningContext?.avg_rating as number | undefined;
    const sentiment = learningContext?.sentiment as string | undefined;
    const isLearning = Boolean(learningContext?.has_feedback);
    return (
      <Card glow={selected && selected >= 4 ? "green" : selected && selected <= 2 ? "red" : "cyan"} className="p-4">
        <div className="flex items-start gap-3">
          <span className="text-2xl">{selected && selected >= 4 ? "✅" : selected && selected <= 2 ? "🔄" : "👍"}</span>
          <div>
            <p className="text-sm font-semibold text-white">
              {selected && selected >= 4 ? "Agents noted your satisfaction" : selected && selected <= 2 ? "Agents will improve" : "Feedback recorded"}
            </p>
            <p className="text-xs text-gray-400 mt-0.5">
              {selected && selected <= 2
                ? "Your feedback is injected into the next analysis prompt — agents will be more specific and evidence-based."
                : "Agents will maintain this reasoning style for future analyses in this domain."}
            </p>
            {isLearning && (
              <div className="mt-2 px-3 py-2 rounded-lg bg-nexus-purple/10 border border-nexus-purple/20">
                <p className="text-xs font-mono text-nexus-purple">
                  {`[NEXUS LEARNING] domain=${domain} avg=${avg}/5 sentiment=${sentiment} — context injected into next Gemini call`}
                </p>
              </div>
            )}
          </div>
        </div>
      </Card>
    );
  }

  return (
    <Card className="p-4">
      <div className="flex items-center gap-2 mb-3">
        <span className="text-sm font-semibold text-white">Rate this analysis</span>
        <span className="text-xs text-gray-500">— agents learn from your feedback</span>
      </div>

      {/* Emoji rating row */}
      <div className="flex gap-2 mb-3">
        {RATINGS.map((r) => (
          <button
            key={r.value}
            onClick={() => setSelected(r.value)}
            title={r.label}
            className={clsx(
              "flex-1 flex flex-col items-center gap-1 py-2 rounded-lg border transition-all",
              selected === r.value
                ? `${r.color} bg-white/5 scale-105 shadow-lg`
                : "border-nexus-border text-gray-600 hover:scale-105"
            )}
          >
            <span className="text-xl">{r.emoji}</span>
            <span className="text-[9px] font-semibold">{r.label}</span>
          </button>
        ))}
      </div>

      {/* Comment box — shows after rating selected */}
      {selected !== null && (
        <div className="mb-3 animate-[fadeIn_0.2s_ease]">
          <textarea
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            placeholder={
              selected <= 2
                ? "What was wrong or too generic? (agents will learn from this)"
                : "What did the agents do well?"
            }
            rows={2}
            className="w-full px-3 py-2 rounded-lg bg-white/5 border border-nexus-border text-sm text-white placeholder-gray-600 focus:outline-none focus:ring-2 focus:ring-nexus-cyan/50 resize-none"
          />
        </div>
      )}

      {/* Learning indicator */}
      <div className="flex items-center gap-2 mb-3 text-xs text-gray-600">
        <span className="w-1.5 h-1.5 rounded-full bg-nexus-purple animate-pulse" />
        Feedback is injected directly into agent Gemini prompts for this domain
      </div>

      {error && <p className="text-xs text-red-400 mb-2">{error}</p>}

      <Button
        onClick={handleSubmit}
        loading={submitting}
        disabled={selected === null}
        size="sm"
        className="w-full"
      >
        Submit Feedback
      </Button>
    </Card>
  );
}
