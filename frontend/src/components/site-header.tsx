"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { ThemeToggle } from "./theme-toggle";
import { cn } from "@/lib/utils";

const links = [
  { href: "/", label: "Home" },
  { href: "/cases", label: "Cases" },
  { href: "/timeline", label: "Timeline" },
  { href: "/analytics", label: "Analytics" },
  { href: "/search", label: "Search" },
];

export function SiteHeader() {
  const pathname = usePathname();
  return (
    <header className="sticky top-0 z-50 border-b border-[var(--border)] bg-[color-mix(in_srgb,var(--background)_82%,transparent)] backdrop-blur-xl">
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-3 md:px-6">
        <Link href="/" className="focus-ring group flex items-center gap-3 rounded-lg">
          <motion.span
            aria-hidden
            className="relative flex h-10 w-10 items-center justify-center rounded-full bg-[var(--pk-green)] text-white"
            whileHover={{ rotate: 12 }}
            transition={{ type: "spring", stiffness: 260, damping: 18 }}
          >
            <svg viewBox="0 0 40 40" className="h-6 w-6" fill="currentColor">
              <path d="M20 6c-1.2 4.8-4.2 7.8-9 9 4.8 1.2 7.8 4.2 9 9 1.2-4.8 4.2-7.8 9-9-4.8-1.2-7.8-4.2-9-9z" />
              <circle cx="29" cy="11" r="1.6" />
            </svg>
          </motion.span>
          <div>
            <p className="font-display text-sm font-semibold tracking-wide text-[var(--pk-green)] dark:text-[var(--pk-gold)] md:text-base">
              Pakistan Public Corruption Atlas
            </p>
            <p className="text-[11px] uppercase tracking-[0.22em] text-[var(--muted)]">1960–2026 · OSINT</p>
          </div>
        </Link>
        <nav aria-label="Primary" className="hidden items-center gap-1 lg:flex">
          {links.map((link) => {
            const active = pathname === link.href;
            return (
              <Link
                key={link.href}
                href={link.href}
                className={cn(
                  "focus-ring rounded-full px-3 py-1.5 text-sm transition",
                  active
                    ? "bg-[var(--pk-green)] text-white"
                    : "text-[var(--muted)] hover:text-[var(--foreground)]"
                )}
              >
                {link.label}
              </Link>
            );
          })}
        </nav>
        <div className="flex items-center gap-2">
          <a
            href="/api/v1/export/json"
            className="focus-ring hidden rounded-full border border-[var(--border)] px-3 py-1.5 text-xs font-medium sm:inline-flex"
          >
            Export JSON
          </a>
          <ThemeToggle />
        </div>
      </div>
      <nav aria-label="Mobile" className="flex gap-1 overflow-x-auto px-4 pb-3 lg:hidden">
        {links.map((link) => (
          <Link
            key={link.href}
            href={link.href}
            className={cn(
              "focus-ring whitespace-nowrap rounded-full px-3 py-1 text-xs",
              pathname === link.href
                ? "bg-[var(--pk-green)] text-white"
                : "border border-[var(--border)] text-[var(--muted)]"
            )}
          >
            {link.label}
          </Link>
        ))}
      </nav>
    </header>
  );
}
