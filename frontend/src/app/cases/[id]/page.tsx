import { DisclaimerBanner } from "@/components/disclaimer";
import { ConfidenceBadge, StatusBadge, TagChip } from "@/components/status-badge";
import { fetchScandal } from "@/lib/api";
import { formatPkr, formatUsd, humanize } from "@/lib/utils";
import Link from "next/link";
import { notFound } from "next/navigation";

export const dynamic = "force-dynamic";

export default async function CaseDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  let detail;
  try {
    detail = await fetchScandal(id);
  } catch {
    notFound();
  }

  return (
    <div className="mx-auto max-w-5xl px-4 py-10 md:px-6">
      <Link href="/cases" className="text-sm text-[var(--pk-cyan)] hover:underline">
        ← All cases
      </Link>
      <div className="mt-4 flex flex-wrap items-center gap-2">
        <StatusBadge status={detail.current_legal_status} />
        <ConfidenceBadge level={detail.confidence_score} />
        {detail.case_type && (
          <span className="rounded-md border border-[var(--pk-green)]/25 bg-[var(--pk-green)]/10 px-2 py-1 text-[11px] font-semibold uppercase tracking-wide text-[var(--pk-green)] dark:border-[var(--pk-gold)]/30 dark:text-[var(--pk-gold)]">
            {humanize(detail.case_type)}
          </span>
        )}
        <span className="text-xs text-[var(--muted)]">{detail.public_id}</span>
        {detail.last_verified && (
          <span className="text-xs text-[var(--muted)]">Verified {detail.last_verified}</span>
        )}
      </div>
      <h1 className="font-display mt-3 text-4xl leading-tight text-[var(--foreground)]">{detail.title}</h1>
      <p className="mt-2 text-sm text-[var(--muted)]">
        {detail.province || "—"}
        {detail.city ? ` · ${detail.city}` : ""} · Started {detail.start_date}
        {detail.end_date ? ` · Ended ${detail.end_date}` : ""}
      </p>
      {detail.legal_outcome && (
        <p className="mt-4 rounded-2xl border border-[var(--border)] bg-white px-4 py-3 text-sm leading-relaxed text-[var(--foreground)] dark:bg-black/20">
          <span className="font-semibold text-[var(--pk-green)] dark:text-[var(--pk-gold)]">Legal outcome: </span>
          {detail.legal_outcome}
        </p>
      )}

      <div className="my-6">
        <DisclaimerBanner />
      </div>

      <section className="glass mb-6 rounded-2xl p-6">
        <h2 className="font-display text-2xl">Executive summary</h2>
        <p className="mt-3 leading-relaxed text-[var(--muted)]">{detail.summary}</p>
        {detail.amount_notes && (
          <p className="mt-3 text-sm italic text-[var(--muted)]">Amount notes: {detail.amount_notes}</p>
        )}
        {(detail.tags?.length ?? 0) > 0 && (
          <div className="mt-4 flex flex-wrap gap-1.5">
            {detail.tags!.map((tag) => (
              <TagChip key={tag} tag={tag} />
            ))}
          </div>
        )}
      </section>

      <section className="mb-6 grid gap-4 sm:grid-cols-2">
        <div className="glass rounded-2xl p-5">
          <h3 className="font-display text-lg">Case metadata</h3>
          <dl className="mt-3 space-y-2 text-sm">
            <div className="flex justify-between gap-3">
              <dt className="text-[var(--muted)]">Institution</dt>
              <dd>{detail.institution || "—"}</dd>
            </div>
            <div className="flex justify-between gap-3">
              <dt className="text-[var(--muted)]">Department</dt>
              <dd>{detail.government_department || "—"}</dd>
            </div>
            <div className="flex justify-between gap-3">
              <dt className="text-[var(--muted)]">Category</dt>
              <dd>{humanize(detail.category)}</dd>
            </div>
            <div className="flex justify-between gap-3">
              <dt className="text-[var(--muted)]">Sector</dt>
              <dd>{detail.sector || "—"}</dd>
            </div>
            <div className="flex justify-between gap-3">
              <dt className="text-[var(--muted)]">Legal outcome</dt>
              <dd>{detail.legal_outcome || detail.status_label || "—"}</dd>
            </div>
            <div className="flex justify-between gap-3">
              <dt className="text-[var(--muted)]">Case type</dt>
              <dd>{detail.case_type ? humanize(detail.case_type) : "—"}</dd>
            </div>
            <div className="flex justify-between gap-3">
              <dt className="text-[var(--muted)]">Loss estimate</dt>
              <dd>
                {detail.financial_loss_estimate?.value != null
                  ? `${detail.financial_loss_estimate.currency || "PKR"} ${Number(detail.financial_loss_estimate.value).toLocaleString()} (${detail.financial_loss_estimate.confidence || "n/a"})`
                  : formatPkr(detail.amount_pkr)}
              </dd>
            </div>
            <div className="flex justify-between gap-3">
              <dt className="text-[var(--muted)]">Amount (PKR)</dt>
              <dd>{formatPkr(detail.amount_pkr)}</dd>
            </div>
            <div className="flex justify-between gap-3">
              <dt className="text-[var(--muted)]">Amount (USD)</dt>
              <dd>{formatUsd(detail.amount_usd)}</dd>
            </div>
            <div className="flex justify-between gap-3">
              <dt className="text-[var(--muted)]">Court</dt>
              <dd>{detail.court_name || "—"}</dd>
            </div>
            <div className="flex justify-between gap-3">
              <dt className="text-[var(--muted)]">Case no.</dt>
              <dd>{detail.case_number || "—"}</dd>
            </div>
          </dl>
        </div>
        <div className="glass rounded-2xl p-5">
          <h3 className="font-display text-lg">Individuals</h3>
          {detail.individuals.length === 0 ? (
            <p className="mt-3 text-sm text-[var(--muted)]">No named individuals in seed record.</p>
          ) : (
            <ul className="mt-3 space-y-3">
              {detail.individuals.map((person) => (
                <li key={person.id} className="text-sm">
                  <p className="font-medium">{person.full_name}</p>
                  <p className="text-[var(--muted)]">
                    {person.position_held || "Position not specified"}
                    {person.political_party ? ` · ${person.political_party}` : ""}
                  </p>
                  {person.role_description && (
                    <p className="mt-1 text-[var(--muted)]">{person.role_description}</p>
                  )}
                </li>
              ))}
            </ul>
          )}
        </div>
      </section>

      <section className="glass mb-6 rounded-2xl p-6">
        <h2 className="font-display text-2xl">Timeline</h2>
        <ol className="mt-4 space-y-4 border-l border-[var(--border)] pl-5">
          {detail.timeline.map((ev) => (
            <li key={ev.id} className="relative">
              <span className="absolute -left-[1.55rem] top-1 h-3 w-3 rounded-full bg-[var(--pk-gold)]" />
              <p className="text-xs uppercase tracking-wider text-[var(--muted)]">{ev.event_date}</p>
              <p className="font-medium">{ev.title}</p>
              {ev.description && <p className="text-sm text-[var(--muted)]">{ev.description}</p>}
              {ev.source_url && (
                <a
                  href={ev.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs text-[var(--pk-cyan)] hover:underline"
                >
                  Event source
                </a>
              )}
              {ev.status_at_event && (
                <div className="mt-1">
                  <StatusBadge status={ev.status_at_event} />
                </div>
              )}
            </li>
          ))}
        </ol>
      </section>

      <section className="glass mb-6 rounded-2xl p-6">
        <h2 className="font-display text-2xl">Citations & sources</h2>
        <p className="mt-1 text-sm text-[var(--muted)]">Every claim should be checked against these primary links.</p>
        <ul className="mt-4 space-y-3">
          {detail.sources.map((src) => (
            <li key={src.id} className="rounded-xl border border-[var(--border)] p-3 text-sm">
              <div className="flex flex-wrap items-center gap-2">
                <a href={src.url} target="_blank" rel="noopener noreferrer" className="font-medium text-[var(--pk-cyan)] hover:underline">
                  {src.title}
                </a>
                {src.is_primary && (
                  <span className="rounded bg-[var(--pk-green)]/10 px-2 py-0.5 text-xs text-[var(--pk-green)] dark:text-[var(--pk-gold)]">
                    Primary
                  </span>
                )}
              </div>
              <p className="text-[var(--muted)]">
                {src.publisher} · {src.source_type}
                {src.published_date ? ` · ${src.published_date}` : ""}
              </p>
              {src.quote_or_claim && <p className="mt-1 italic text-[var(--muted)]">Supports: {src.quote_or_claim}</p>}
            </li>
          ))}
        </ul>
      </section>

      {detail.documents.length > 0 && (
        <section className="glass mb-6 rounded-2xl p-6">
          <h2 className="font-display text-2xl">Supporting documents</h2>
          <ul className="mt-3 space-y-2 text-sm">
            {detail.documents.map((doc) => (
              <li key={doc.id}>
                {doc.url ? (
                  <a href={doc.url} target="_blank" rel="noopener noreferrer" className="text-[var(--pk-cyan)] hover:underline">
                    {doc.title}
                  </a>
                ) : (
                  doc.title
                )}
                {doc.document_type ? ` · ${doc.document_type}` : ""}
              </li>
            ))}
          </ul>
        </section>
      )}

      {detail.related_scandal_ids.length > 0 && (
        <section className="glass rounded-2xl p-6">
          <h2 className="font-display text-2xl">Related scandals</h2>
          <ul className="mt-3 flex flex-wrap gap-2">
            {detail.related_scandal_ids.map((rid) => (
              <li key={rid}>
                <Link href={`/cases/${rid}`} className="rounded-full border border-[var(--border)] px-3 py-1 text-sm hover:bg-[var(--pk-green)]/10">
                  Related record
                </Link>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
