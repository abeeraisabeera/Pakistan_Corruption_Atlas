import Link from "next/link";
import type { ScandalListItem } from "@/lib/types";
import { ConfidenceBadge, StatusBadge, TagChip } from "./status-badge";
import { formatPkr, humanize } from "@/lib/utils";

export function CaseCard({ item }: { item: ScandalListItem }) {
  const tags = (item.tags || []).slice(0, 4);
  const outcome =
    item.legal_outcome && item.legal_outcome.length > 48 ? item.legal_outcome : null;

  return (
    <article className="glass group rounded-2xl p-5 transition hover:-translate-y-0.5">
      <div className="mb-3 flex flex-wrap items-center gap-2">
        <StatusBadge status={item.current_legal_status} />
        <ConfidenceBadge level={item.confidence_score} />
        {item.case_type && (
          <span className="rounded-md border border-[var(--pk-green)]/25 bg-[var(--pk-green)]/10 px-2 py-1 text-[11px] font-semibold uppercase tracking-wide text-[var(--pk-green)] dark:border-[var(--pk-gold)]/30 dark:text-[var(--pk-gold)]">
            {humanize(item.case_type)}
          </span>
        )}
        <span className="text-xs text-[var(--muted)]">{item.source_count} sources</span>
      </div>
      <p className="mb-1 text-xs font-semibold uppercase tracking-[0.16em] text-[var(--pk-cyan)]">
        {item.public_id}
      </p>
      <h3 className="font-display text-lg leading-snug text-[var(--foreground)]">
        <Link href={`/cases/${item.public_id}`} className="focus-ring rounded hover:underline">
          {item.title}
        </Link>
      </h3>
      <p className="mt-2 line-clamp-3 text-sm leading-relaxed text-[var(--muted)]">{item.summary}</p>
      {outcome && (
        <p className="mt-3 rounded-xl border border-[var(--border)] bg-white/80 px-3 py-2 text-xs leading-relaxed text-[var(--foreground)] dark:bg-black/20">
          <span className="font-semibold text-[var(--pk-green)] dark:text-[var(--pk-gold)]">Outcome: </span>
          {outcome}
        </p>
      )}
      {tags.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-1.5">
          {tags.map((tag) => (
            <TagChip key={tag} tag={tag} />
          ))}
        </div>
      )}
      <dl className="mt-4 grid grid-cols-2 gap-2 text-xs">
        <div>
          <dt className="uppercase tracking-wider text-[var(--muted)]">Province</dt>
          <dd className="font-medium text-[var(--foreground)]">{item.province || "—"}</dd>
        </div>
        <div>
          <dt className="uppercase tracking-wider text-[var(--muted)]">Category</dt>
          <dd className="font-medium text-[var(--foreground)]">{humanize(item.category)}</dd>
        </div>
        <div>
          <dt className="uppercase tracking-wider text-[var(--muted)]">Year</dt>
          <dd className="font-medium text-[var(--foreground)]">{new Date(item.start_date).getFullYear()}</dd>
        </div>
        <div>
          <dt className="uppercase tracking-wider text-[var(--muted)]">Amount</dt>
          <dd className="font-medium text-[var(--foreground)]">{formatPkr(item.amount_pkr)}</dd>
        </div>
      </dl>
    </article>
  );
}
