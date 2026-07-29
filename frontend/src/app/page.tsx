import { CaseCard } from "@/components/case-card";
import { CategoryPie, ProvinceChart, YearChart } from "@/components/charts";
import { DisclaimerBanner } from "@/components/disclaimer";
import { fetchDashboard } from "@/lib/api";
import { formatPkr, formatUsd } from "@/lib/utils";
import Link from "next/link";

export const dynamic = "force-dynamic";

export default async function HomePage() {
  let stats = null;
  let error: string | null = null;
  try {
    stats = await fetchDashboard();
  } catch (e) {
    error = e instanceof Error ? e.message : "Failed to load dashboard";
  }

  return (
    <div className="mx-auto max-w-7xl px-4 pb-16 pt-8 md:px-6">
      <section className="relative mb-12 min-h-[68vh] overflow-hidden rounded-[2rem] border border-[var(--border)]">
        <div
          className="absolute inset-0 bg-[linear-gradient(135deg,#01411C_0%,#0a5c2e_42%,#013318_100%)]"
          aria-hidden
        />
        <div
          className="absolute inset-0 opacity-30"
          style={{
            backgroundImage:
              "url(\"data:image/svg+xml,%3Csvg width='80' height='80' viewBox='0 0 80 80' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M40 0l40 40-40 40L0 40z' fill='none' stroke='%23ffffff' stroke-opacity='0.25'/%3E%3C/svg%3E\")",
          }}
          aria-hidden
        />
        <div className="relative z-10 flex min-h-[68vh] flex-col justify-end px-6 py-12 text-white md:px-12 md:py-16">
          <p className="mb-3 text-xs uppercase tracking-[0.35em] text-white/70">Public OSINT · 1960–2026</p>
          <h1 className="font-display max-w-4xl text-4xl font-semibold leading-[1.05] md:text-6xl">
            Pakistan Public Corruption Atlas
          </h1>
          <p className="mt-4 max-w-2xl text-base text-white/85 md:text-lg">
            A journalism and research platform that collects, verifies, and visualizes publicly documented
            proceedings — never inventing facts, never equating allegation with guilt.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link
              href="/cases"
              className="focus-ring rounded-full bg-white px-5 py-2.5 text-sm font-bold text-[#01411C] hover:bg-[#f0f7f2]"
            >
              Browse cases
            </Link>
            <Link
              href="/analytics"
              className="focus-ring rounded-full border-2 border-white/80 bg-white/10 px-5 py-2.5 text-sm font-bold text-white hover:bg-white/20"
            >
              Open analytics
            </Link>
          </div>
        </div>
      </section>

      <div className="mb-8">
        <DisclaimerBanner />
      </div>

      {error && (
        <div className="glass mb-8 rounded-2xl p-6 text-sm">
          <p className="font-semibold text-rose-700 dark:text-rose-300">API unavailable</p>
          <p className="mt-1 text-[var(--muted)]">
            Start the FastAPI backend (`uvicorn app.main:app --port 7860`). {error}
          </p>
        </div>
      )}

      {stats && (
        <>
          <section className="mb-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-4" aria-label="Key totals">
            {[
              { label: "Documented scandals", value: String(stats.total_scandals) },
              { label: "Estimated value (PKR)", value: formatPkr(stats.total_estimated_pkr) },
              { label: "Estimated value (USD)", value: formatUsd(stats.total_estimated_usd) },
              {
                label: "Resolved outcomes tracked",
                value: String(stats.conviction_stats.resolved),
              },
            ].map((stat) => (
              <div key={stat.label} className="glass rounded-2xl p-5">
                <p className="text-xs uppercase tracking-[0.18em] text-[var(--muted)]">{stat.label}</p>
                <p className="mt-2 font-display text-3xl font-semibold text-[var(--pk-green)] dark:text-[var(--pk-gold)]">
                  {stat.value}
                </p>
              </div>
            ))}
          </section>

          <section className="mb-10 grid gap-6 lg:grid-cols-2">
            <div className="glass rounded-2xl p-5">
              <h2 className="font-display text-xl">Cases by year</h2>
              <YearChart data={stats.by_year} />
            </div>
            <div className="glass rounded-2xl p-5">
              <h2 className="font-display text-xl">Cases by province</h2>
              <ProvinceChart data={stats.by_province} />
            </div>
            <div className="glass rounded-2xl p-5">
              <h2 className="font-display text-xl">Category mix</h2>
              <CategoryPie data={stats.by_category} />
            </div>
            <div className="glass rounded-2xl p-5">
              <h2 className="font-display mb-3 text-xl">Case types</h2>
              <ul className="space-y-2">
                {(stats.by_case_type || []).map((row) => (
                  <li key={row.case_type} className="flex items-center justify-between gap-3 text-sm">
                    <span className="capitalize">{row.case_type.replace(/_/g, " ")}</span>
                    <span className="rounded-md bg-[var(--pk-green)]/10 px-2 py-0.5 text-[var(--pk-green)] dark:text-[var(--pk-gold)]">
                      {row.count}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
            <div className="glass rounded-2xl p-5">
              <h2 className="font-display mb-3 text-xl">Institutions (top)</h2>
              <ul className="space-y-2">
                {stats.by_institution.map((row) => (
                  <li key={row.institution} className="flex items-center justify-between gap-3 text-sm">
                    <span>{row.institution}</span>
                    <span className="rounded-md bg-[var(--pk-green)]/10 px-2 py-0.5 text-[var(--pk-green)] dark:text-[var(--pk-gold)]">
                      {row.count}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          </section>

          <section>
            <div className="mb-4 flex items-end justify-between gap-3">
              <h2 className="font-display text-2xl">Latest additions</h2>
              <Link href="/cases" className="text-sm text-[var(--pk-cyan)] hover:underline">
                View all
              </Link>
            </div>
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
              {stats.latest.map((item) => (
                <CaseCard key={item.id} item={item} />
              ))}
            </div>
          </section>
        </>
      )}
    </div>
  );
}
