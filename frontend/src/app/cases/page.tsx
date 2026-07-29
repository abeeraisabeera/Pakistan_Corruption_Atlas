import { CaseCard } from "@/components/case-card";
import { DisclaimerBanner } from "@/components/disclaimer";
import { PrimaryButton } from "@/components/status-badge";
import { fetchScandals } from "@/lib/api";
import Link from "next/link";

export const dynamic = "force-dynamic";

const CATEGORIES = [
  "procurement",
  "money_laundering",
  "bribery",
  "kickbacks",
  "land_scam",
  "tax_fraud",
  "state_asset_misuse",
  "election_finance",
  "public_fund_embezzlement",
  "ghost_employees",
  "illegal_contracts",
  "infrastructure_fraud",
  "customs",
  "police_corruption",
  "judicial_misconduct",
  "military_procurement",
  "state_owned_enterprises",
  "misuse_of_authority",
];

const STATUSES = [
  "allegation",
  "investigation",
  "charge",
  "trial",
  "conviction",
  "acquittal",
  "case_dismissed",
  "pending",
  "official_inquiry",
  "investigative_journalism_report",
  "mixed",
  "civil_settlement",
  "closed",
  "settled_no_criminal_reference",
  "reference_withdrawal_sought",
];

const CASE_TYPES = ["criminal", "civil", "judicial_review", "audit", "journalistic", "parliamentary"];

export default async function CasesPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | undefined>>;
}) {
  const params = await searchParams;
  const page = Number(params.page || 1);
  let data = null;
  let error: string | null = null;
  try {
    data = await fetchScandals({
      q: params.q,
      province: params.province,
      category: params.category,
      status: params.status,
      case_type: params.case_type,
      tag: params.tag,
      year_from: params.year_from,
      year_to: params.year_to,
      page,
      page_size: 12,
    });
  } catch (e) {
    error = e instanceof Error ? e.message : "Failed to load";
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-10 md:px-6">
      <h1 className="font-display text-4xl">Documented cases</h1>
      <p className="mt-2 max-w-2xl text-[var(--muted)]">
        Filter publicly sourced records. Status labels reflect procedural stages reported in citations.
      </p>
      <div className="my-6">
        <DisclaimerBanner compact />
      </div>

      <form className="glass mb-8 grid gap-3 rounded-2xl p-4 md:grid-cols-3 lg:grid-cols-6" method="get">
        <label className="text-xs uppercase tracking-wider text-[var(--muted)]">
          Search
          <input
            name="q"
            defaultValue={params.q || ""}
            className="mt-1 w-full rounded-xl border border-[var(--border)] bg-transparent px-3 py-2 text-sm"
          />
        </label>
        <label className="text-xs uppercase tracking-wider text-[var(--muted)]">
          Province
          <input
            name="province"
            defaultValue={params.province || ""}
            className="mt-1 w-full rounded-xl border border-[var(--border)] bg-transparent px-3 py-2 text-sm"
          />
        </label>
        <label className="text-xs uppercase tracking-wider text-[var(--muted)]">
          Category
          <select
            name="category"
            defaultValue={params.category || ""}
            className="mt-1 w-full rounded-xl border border-[var(--border)] bg-transparent px-3 py-2 text-sm"
          >
            <option value="">All</option>
            {CATEGORIES.map((c) => (
              <option key={c} value={c}>
                {c.replace(/_/g, " ")}
              </option>
            ))}
          </select>
        </label>
        <label className="text-xs uppercase tracking-wider text-[var(--muted)]">
          Status
          <select
            name="status"
            defaultValue={params.status || ""}
            className="mt-1 w-full rounded-xl border border-[var(--border)] bg-transparent px-3 py-2 text-sm"
          >
            <option value="">All</option>
            {STATUSES.map((s) => (
              <option key={s} value={s}>
                {s.replace(/_/g, " ")}
              </option>
            ))}
          </select>
        </label>
        <label className="text-xs uppercase tracking-wider text-[var(--muted)]">
          Case type
          <select
            name="case_type"
            defaultValue={params.case_type || ""}
            className="mt-1 w-full rounded-xl border border-[var(--border)] bg-transparent px-3 py-2 text-sm"
          >
            <option value="">All</option>
            {CASE_TYPES.map((c) => (
              <option key={c} value={c}>
                {c.replace(/_/g, " ")}
              </option>
            ))}
          </select>
        </label>
        <label className="text-xs uppercase tracking-wider text-[var(--muted)]">
          Tag
          <input
            name="tag"
            defaultValue={params.tag || ""}
            placeholder="NAB, land scam…"
            className="mt-1 w-full rounded-xl border border-[var(--border)] bg-transparent px-3 py-2 text-sm"
          />
        </label>
        <label className="text-xs uppercase tracking-wider text-[var(--muted)]">
          Year from
          <input
            name="year_from"
            type="number"
            min={1960}
            max={2026}
            defaultValue={params.year_from || ""}
            className="mt-1 w-full rounded-xl border border-[var(--border)] bg-transparent px-3 py-2 text-sm"
          />
        </label>
        <div className="flex items-end">
          <PrimaryButton type="submit" className="w-full">
            Apply filters
          </PrimaryButton>
        </div>
      </form>

      {error && <p className="text-sm text-rose-600">{error}</p>}

      {data && (
        <>
          <p className="mb-4 text-sm text-[var(--muted)]">{data.total} records</p>
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {data.items.map((item) => (
              <CaseCard key={item.id} item={item} />
            ))}
          </div>
          <div className="mt-8 flex items-center justify-center gap-3">
            {page > 1 && (
              <Link
                href={`/cases?${new URLSearchParams({ ...params, page: String(page - 1) } as Record<string, string>).toString()}`}
                className="rounded-full border border-[var(--border)] px-4 py-2 text-sm"
              >
                Previous
              </Link>
            )}
            <span className="text-sm text-[var(--muted)]">
              Page {data.page} / {data.pages}
            </span>
            {page < data.pages && (
              <Link
                href={`/cases?${new URLSearchParams({ ...params, page: String(page + 1) } as Record<string, string>).toString()}`}
                className="rounded-full border border-[var(--border)] px-4 py-2 text-sm"
              >
                Next
              </Link>
            )}
          </div>
        </>
      )}
    </div>
  );
}
