import { DISCLAIMER } from "@/lib/types";

export function DisclaimerBanner({ compact = false }: { compact?: boolean }) {
  return (
    <aside
      role="note"
      aria-label="Research disclaimer"
      className="glass rounded-2xl px-4 py-3 text-sm leading-relaxed text-[var(--muted)]"
    >
      {!compact && (
        <p className="mb-1 font-display text-xs font-semibold uppercase tracking-[0.18em] text-[var(--pk-green)] dark:text-[var(--pk-gold)]">
          Ethics & methodology
        </p>
      )}
      <p>{DISCLAIMER}</p>
    </aside>
  );
}
