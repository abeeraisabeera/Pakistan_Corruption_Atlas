import type { ReactNode } from "react";
import type { ConfidenceLevel, LegalStatus } from "@/lib/types";
import { STATUS_LABELS } from "@/lib/types";
import { cn } from "@/lib/utils";

/**
 * Light mode uses solid pastel fills + near-black ink for WCAG contrast.
 * Avoid low-opacity tint chips that wash out on glass cards.
 */
const statusTone: Record<LegalStatus, string> = {
  allegation:
    "border-[#b45309] bg-[#ffedd5] text-[#7c2d12] dark:border-amber-400/50 dark:bg-amber-500/25 dark:text-amber-100",
  investigation:
    "border-[#0369a1] bg-[#e0f2fe] text-[#0c4a6e] dark:border-sky-400/50 dark:bg-sky-500/25 dark:text-sky-100",
  charge:
    "border-[#c2410c] bg-[#ffedd5] text-[#7c2d12] dark:border-orange-400/50 dark:bg-orange-500/25 dark:text-orange-100",
  trial:
    "border-[#4338ca] bg-[#e0e7ff] text-[#312e81] dark:border-indigo-400/50 dark:bg-indigo-500/25 dark:text-indigo-100",
  conviction:
    "border-[#be123c] bg-[#ffe4e6] text-[#881337] dark:border-rose-400/50 dark:bg-rose-500/25 dark:text-rose-100",
  acquittal:
    "border-[#047857] bg-[#d1fae5] text-[#064e3b] dark:border-emerald-400/50 dark:bg-emerald-500/25 dark:text-emerald-100",
  case_dismissed:
    "border-[#57534e] bg-[#e7e5e4] text-[#1c1917] dark:border-stone-400/50 dark:bg-stone-500/25 dark:text-stone-100",
  pending:
    "border-[#a16207] bg-[#fef9c3] text-[#713f12] dark:border-yellow-400/50 dark:bg-yellow-500/25 dark:text-yellow-100",
  official_inquiry:
    "border-[#0f766e] bg-[#99f6e4] text-[#042f2e] dark:border-teal-400/50 dark:bg-teal-500/25 dark:text-teal-50",
  investigative_journalism_report:
    "border-[#a21caf] bg-[#fae8ff] text-[#701a75] dark:border-fuchsia-400/50 dark:bg-fuchsia-500/25 dark:text-fuchsia-100",
  mixed:
    "border-[#6d28d9] bg-[#ede9fe] text-[#4c1d95] dark:border-violet-400/50 dark:bg-violet-500/25 dark:text-violet-100",
  civil_settlement:
    "border-[#0e7490] bg-[#cffafe] text-[#083344] dark:border-cyan-400/50 dark:bg-cyan-500/25 dark:text-cyan-100",
  closed:
    "border-[#57534e] bg-[#e7e5e4] text-[#1c1917] dark:border-stone-400/50 dark:bg-stone-500/25 dark:text-stone-100",
  settled_no_criminal_reference:
    "border-[#4d7c0f] bg-[#ecfccb] text-[#365314] dark:border-lime-400/50 dark:bg-lime-500/25 dark:text-lime-100",
  reference_withdrawal_sought:
    "border-[#c2410c] bg-[#ffedd5] text-[#7c2d12] dark:border-orange-400/50 dark:bg-orange-500/25 dark:text-orange-100",
};

function shortLabel(status: LegalStatus, label?: string | null) {
  const fromEnum = STATUS_LABELS[status];
  if (label && label.length <= 48 && !label.includes(". ")) return label;
  return fromEnum || status.replace(/_/g, " ");
}

export function StatusBadge({ status, label }: { status: LegalStatus; label?: string | null }) {
  return (
    <span
      className={cn(
        "inline-flex max-w-full shrink-0 items-center rounded-md border px-2.5 py-1 text-xs font-bold tracking-wide",
        statusTone[status] || "border-[#57534e] bg-[#e7e5e4] text-[#1c1917]"
      )}
    >
      {shortLabel(status, label)}
    </span>
  );
}

export function ConfidenceBadge({ level }: { level: ConfidenceLevel }) {
  const tone =
    level === "high"
      ? "text-[#064e3b] dark:text-emerald-300"
      : level === "medium"
        ? "text-[#713f12] dark:text-amber-300"
        : "text-[#881337] dark:text-rose-300";
  return (
    <span className={cn("text-xs font-bold uppercase tracking-wider", tone)}>
      Confidence: {level}
    </span>
  );
}

export function TagChip({ tag }: { tag: string }) {
  return (
    <span className="rounded-md border border-[var(--border)] bg-white px-2 py-0.5 text-[11px] font-semibold text-[var(--foreground)] dark:bg-transparent dark:font-medium dark:text-[var(--muted)]">
      {tag}
    </span>
  );
}

/** Primary CTA — distinct in light vs dark */
export function PrimaryButton({
  children,
  className,
  type = "button",
  disabled,
}: {
  children: ReactNode;
  className?: string;
  type?: "button" | "submit" | "reset";
  disabled?: boolean;
}) {
  return (
    <button
      type={type}
      disabled={disabled}
      className={cn(
        "focus-ring inline-flex items-center justify-center rounded-xl px-4 py-2.5 text-sm font-bold transition",
        "bg-[#01411C] text-white hover:bg-[#0a5c2e]",
        "dark:bg-[#c4a35a] dark:text-[#06140c] dark:hover:bg-[#d4b56e]",
        "disabled:cursor-not-allowed disabled:opacity-60",
        className
      )}
    >
      {children}
    </button>
  );
}
