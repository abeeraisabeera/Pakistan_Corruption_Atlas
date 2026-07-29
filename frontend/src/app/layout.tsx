import { SiteHeader } from "@/components/site-header";
import { ThemeProvider } from "@/components/theme-provider";
import type { Metadata } from "next";
import { Cormorant_Garamond, Source_Serif_4 } from "next/font/google";
import "./globals.css";

const display = Cormorant_Garamond({
  subsets: ["latin"],
  weight: ["500", "600", "700"],
  variable: "--font-display",
});

const body = Source_Serif_4({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-body",
});

export const metadata: Metadata = {
  title: "Pakistan Public Corruption Atlas (1960–2026)",
  description:
    "OSINT research dashboard aggregating publicly documented corruption-related proceedings. Inclusion does not imply guilt.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${display.variable} ${body.variable} geo-bg antialiased`}>
        <ThemeProvider>
          <a
            href="#main"
            className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-[100] focus:rounded focus:bg-white focus:px-3 focus:py-2"
          >
            Skip to content
          </a>
          <SiteHeader />
          <main id="main">{children}</main>
          <footer className="mx-auto max-w-7xl px-4 py-10 text-sm text-[var(--muted)] md:px-6">
            <p>
              Pakistan Public Corruption Atlas — research & education only. Not affiliated with any political party or
              government body.
            </p>
          </footer>
        </ThemeProvider>
      </body>
    </html>
  );
}
