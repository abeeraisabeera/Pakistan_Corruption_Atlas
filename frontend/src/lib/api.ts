import type { DashboardStats, PaginatedScandals, ScandalDetail } from "./types";

/** Server-side / SSR: talk to the FastAPI origin directly. */
const UPSTREAM = (process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:7860").replace(/\/$/, "");

/**
 * Browser: same-origin "" so fetch hits Next rewrites (/api → upstream).
 * Server: absolute upstream URL (no CORS involved).
 */
function apiBase(): string {
  if (typeof window !== "undefined") return "";
  return UPSTREAM;
}

async function getJson<T>(path: string, init?: RequestInit): Promise<T> {
  const isServer = typeof window === "undefined";
  // Public read API — never send credentials or API keys from the browser.
  const res = await fetch(`${apiBase()}${path}`, {
    ...init,
    credentials: "omit",
    headers: { Accept: "application/json", ...(init?.headers || {}) },
    ...(isServer ? { next: { revalidate: 60 } } : { cache: "no-store" as RequestCache }),
  });
  if (!res.ok) {
    throw new Error(`API ${path} failed: ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export function apiUrl(path: string) {
  return `${apiBase()}${path}`;
}

export async function fetchDashboard(): Promise<DashboardStats> {
  return getJson("/api/v1/stats/dashboard");
}

export async function fetchScandals(params: Record<string, string | number | undefined> = {}) {
  const qs = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== "" && v !== null) qs.set(k, String(v));
  });
  const q = qs.toString();
  return getJson<PaginatedScandals>(`/api/v1/scandals${q ? `?${q}` : ""}`);
}

export async function fetchScandal(id: string): Promise<ScandalDetail> {
  return getJson(`/api/v1/scandals/${encodeURIComponent(id)}`);
}

export async function fetchAnalytics() {
  return getJson<Record<string, unknown>>("/api/v1/analytics/trends");
}

export async function fetchSankey() {
  return getJson<{ nodes: { name: string }[]; links: { source: number; target: number; value: number }[] }>(
    "/api/v1/analytics/sankey"
  );
}
