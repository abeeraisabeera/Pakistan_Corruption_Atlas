"use client";

import { CaseCard } from "@/components/case-card";
import { DisclaimerBanner } from "@/components/disclaimer";
import { fetchScandals } from "@/lib/api";
import type { ScandalListItem } from "@/lib/types";
import { motion } from "framer-motion";
import { useEffect, useMemo, useState } from "react";

export default function TimelinePage() {
  const [items, setItems] = useState<ScandalListItem[]>([]);
  const [yearFrom, setYearFrom] = useState(1960);
  const [yearTo, setYearTo] = useState(2026);
  const [status, setStatus] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchScandals({ year_from: yearFrom, year_to: yearTo, status: status || undefined, page_size: 100 })
      .then((d) => setItems(d.items))
      .catch((e) => setError(e.message));
  }, [yearFrom, yearTo, status]);

  const byYear = useMemo(() => {
    const map = new Map<number, ScandalListItem[]>();
    items.forEach((item) => {
      const y = new Date(item.start_date).getFullYear();
      if (!map.has(y)) map.set(y, []);
      map.get(y)!.push(item);
    });
    return [...map.entries()].sort((a, b) => a[0] - b[0]);
  }, [items]);

  return (
    <div className="mx-auto max-w-7xl px-4 py-10 md:px-6">
      <h1 className="font-display text-4xl">Interactive timeline</h1>
      <p className="mt-2 text-[var(--muted)]">Zoom the window with year filters. Each entry retains its legal-status label.</p>
      <div className="my-6">
        <DisclaimerBanner compact />
      </div>

      <div className="glass mb-8 grid gap-4 rounded-2xl p-4 md:grid-cols-3">
        <label className="text-sm">
          From {yearFrom}
          <input
            type="range"
            min={1960}
            max={2026}
            value={yearFrom}
            onChange={(e) => setYearFrom(Math.min(Number(e.target.value), yearTo))}
            className="mt-2 w-full"
            aria-label="Timeline start year"
          />
        </label>
        <label className="text-sm">
          To {yearTo}
          <input
            type="range"
            min={1960}
            max={2026}
            value={yearTo}
            onChange={(e) => setYearTo(Math.max(Number(e.target.value), yearFrom))}
            className="mt-2 w-full"
            aria-label="Timeline end year"
          />
        </label>
        <label className="text-sm">
          Status filter
          <select
            value={status}
            onChange={(e) => setStatus(e.target.value)}
            className="mt-2 w-full rounded-xl border border-[var(--border)] bg-transparent px-3 py-2"
          >
            <option value="">All statuses</option>
            <option value="allegation">Alleged</option>
            <option value="investigation">Under Investigation</option>
            <option value="conviction">Convicted</option>
            <option value="acquittal">Acquitted</option>
            <option value="official_inquiry">Official Inquiry</option>
            <option value="investigative_journalism_report">Investigative Journalism</option>
          </select>
        </label>
      </div>

      {error && <p className="text-sm text-rose-600">{error}</p>}

      <div className="space-y-10">
        {byYear.map(([year, cases]) => (
          <motion.section
            key={year}
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-40px" }}
            transition={{ duration: 0.35 }}
          >
            <h2 className="font-display mb-4 text-3xl text-[var(--pk-green)] dark:text-[var(--pk-gold)]">{year}</h2>
            <div className="grid gap-4 md:grid-cols-2">
              {cases.map((item) => (
                <CaseCard key={item.id} item={item} />
              ))}
            </div>
          </motion.section>
        ))}
      </div>
    </div>
  );
}
