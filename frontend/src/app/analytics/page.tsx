"use client";

import { SankeyChart, StatusChart, YearChart } from "@/components/charts";
import { DisclaimerBanner } from "@/components/disclaimer";
import { fetchAnalytics, fetchSankey } from "@/lib/api";
import { useEffect, useState } from "react";

export default function AnalyticsPage() {
  const [trends, setTrends] = useState<Record<string, unknown> | null>(null);
  const [sankey, setSankey] = useState<{
    nodes: { name: string }[];
    links: { source: number; target: number; value: number }[];
  } | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([fetchAnalytics(), fetchSankey()])
      .then(([t, s]) => {
        setTrends(t);
        setSankey(s);
      })
      .catch((e) => setError(e.message));
  }, []);

  const byYear = (trends?.by_year as { year: number; count: number }[]) || [];
  const byStatus = (trends?.by_status as { status: string; count: number }[]) || [];
  const institutions = (trends?.by_institution as { institution: string; count: number }[]) || [];
  const conviction = trends?.conviction_stats as
    | {
        convictions: number;
        acquittals: number;
        dismissed: number;
        conviction_rate: number | null;
        note: string;
      }
    | undefined;
  const durations =
    (trends?.investigation_duration as {
      public_id: string;
      title: string;
      days: number;
      status: string;
    }[]) || [];

  return (
    <div className="mx-auto max-w-7xl px-4 py-10 md:px-6">
      <h1 className="font-display text-4xl">Analytics</h1>
      <p className="mt-2 text-[var(--muted)]">
        Trends, recurring institutions, and documented money-flow Sankey diagrams.
      </p>
      <div className="my-6">
        <DisclaimerBanner />
      </div>
      {error && <p className="text-sm text-rose-600">{error}</p>}

      <section className="mb-8 grid gap-6 lg:grid-cols-2">
        <div className="glass rounded-2xl p-5">
          <h2 className="font-display text-xl">Cases per year</h2>
          <YearChart data={byYear} />
        </div>
        <div className="glass rounded-2xl p-5">
          <h2 className="font-display text-xl">Status breakdown</h2>
          <StatusChart data={byStatus} />
        </div>
      </section>

      <section className="glass mb-8 rounded-2xl p-5">
        <h2 className="font-display text-xl">Conviction / acquittal snapshot</h2>
        {conviction && (
          <div className="mt-3 grid gap-3 sm:grid-cols-4 text-sm">
            <div>
              <p className="text-[var(--muted)]">Convictions</p>
              <p className="font-display text-2xl">{conviction.convictions}</p>
            </div>
            <div>
              <p className="text-[var(--muted)]">Acquittals</p>
              <p className="font-display text-2xl">{conviction.acquittals}</p>
            </div>
            <div>
              <p className="text-[var(--muted)]">Dismissed</p>
              <p className="font-display text-2xl">{conviction.dismissed}</p>
            </div>
            <div>
              <p className="text-[var(--muted)]">Rate (dataset)</p>
              <p className="font-display text-2xl">
                {conviction.conviction_rate == null
                  ? "—"
                  : `${(conviction.conviction_rate * 100).toFixed(1)}%`}
              </p>
            </div>
          </div>
        )}
        <p className="mt-3 text-xs text-[var(--muted)]">{conviction?.note}</p>
      </section>

      <section className="glass mb-8 rounded-2xl p-5">
        <h2 className="font-display mb-3 text-xl">Recurring institutions</h2>
        <ul className="grid gap-2 md:grid-cols-2">
          {institutions.map((row) => (
            <li
              key={row.institution}
              className="flex justify-between rounded-xl border border-[var(--border)] px-3 py-2 text-sm"
            >
              <span>{row.institution}</span>
              <span>{row.count}</span>
            </li>
          ))}
        </ul>
      </section>

      <section className="glass mb-8 rounded-2xl p-5">
        <h2 className="font-display mb-2 text-xl">Investigation duration (documented span)</h2>
        <p className="mb-3 text-xs text-[var(--muted)]">
          Days between recorded start and end dates only.
        </p>
        <ul className="max-h-64 space-y-2 overflow-auto text-sm">
          {durations.map((d) => (
            <li
              key={d.public_id}
              className="flex justify-between gap-3 border-b border-[var(--border)] py-2"
            >
              <span className="line-clamp-1">{d.title}</span>
              <span className="shrink-0 text-[var(--muted)]">{d.days} days</span>
            </li>
          ))}
        </ul>
      </section>

      <section className="glass rounded-2xl p-5">
        <h2 className="font-display mb-3 text-xl">Money flow Sankey</h2>
        <p className="mb-3 text-xs text-[var(--muted)]">
          Province → category → status using documented amounts only.
        </p>
        {sankey && <SankeyChart nodes={sankey.nodes} links={sankey.links} />}
      </section>
    </div>
  );
}
