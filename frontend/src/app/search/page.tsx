"use client";

import { CaseCard } from "@/components/case-card";
import { DisclaimerBanner } from "@/components/disclaimer";
import { PrimaryButton } from "@/components/status-badge";
import { fetchScandals } from "@/lib/api";
import type { ScandalListItem } from "@/lib/types";
import { useState } from "react";

export default function SearchPage() {
  const [q, setQ] = useState("");
  const [individual, setIndividual] = useState("");
  const [institution, setInstitution] = useState("");
  const [items, setItems] = useState<ScandalListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const data = await fetchScandals({
        q: q || undefined,
        individual: individual || undefined,
        institution: institution || undefined,
        page_size: 30,
      });
      setItems(data.items);
      setTotal(data.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Search failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-10 md:px-6">
      <h1 className="font-display text-4xl">Search</h1>
      <p className="mt-2 text-[var(--muted)]">Search by keyword, individual, or institution across verified records.</p>
      <div className="my-6">
        <DisclaimerBanner compact />
      </div>

      <form onSubmit={onSubmit} className="glass mb-8 grid gap-3 rounded-2xl p-4 md:grid-cols-4">
        <label className="text-xs uppercase tracking-wider text-[var(--muted)] md:col-span-2">
          Keyword
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            className="mt-1 w-full rounded-xl border border-[var(--border)] bg-transparent px-3 py-2 text-sm"
            placeholder="Title, summary, public ID…"
          />
        </label>
        <label className="text-xs uppercase tracking-wider text-[var(--muted)]">
          Individual
          <input
            value={individual}
            onChange={(e) => setIndividual(e.target.value)}
            className="mt-1 w-full rounded-xl border border-[var(--border)] bg-transparent px-3 py-2 text-sm"
          />
        </label>
        <label className="text-xs uppercase tracking-wider text-[var(--muted)]">
          Institution
          <input
            value={institution}
            onChange={(e) => setInstitution(e.target.value)}
            className="mt-1 w-full rounded-xl border border-[var(--border)] bg-transparent px-3 py-2 text-sm"
          />
        </label>
        <PrimaryButton type="submit" className="md:col-span-4 md:w-fit" disabled={loading}>
          {loading ? "Searching…" : "Search"}
        </PrimaryButton>
      </form>

      {error && <p className="text-sm text-rose-600">{error}</p>}
      <p className="mb-4 text-sm text-[var(--muted)]">{total} results</p>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {items.map((item) => (
          <CaseCard key={item.id} item={item} />
        ))}
      </div>
    </div>
  );
}
