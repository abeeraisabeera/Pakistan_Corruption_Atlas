import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatPkr(value?: number | null) {
  if (value == null) return "—";
  if (value >= 1_000_000_000_000) return `PKR ${(value / 1_000_000_000_000).toFixed(2)}T`;
  if (value >= 1_000_000_000) return `PKR ${(value / 1_000_000_000).toFixed(2)}B`;
  if (value >= 1_000_000) return `PKR ${(value / 1_000_000).toFixed(2)}M`;
  return `PKR ${value.toLocaleString()}`;
}

export function formatUsd(value?: number | null) {
  if (value == null) return "—";
  if (value >= 1_000_000_000) return `$${(value / 1_000_000_000).toFixed(2)}B`;
  if (value >= 1_000_000) return `$${(value / 1_000_000).toFixed(2)}M`;
  return `$${value.toLocaleString()}`;
}

export function humanize(value: string) {
  return value.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}
