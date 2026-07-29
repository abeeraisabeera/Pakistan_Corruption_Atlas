export type LegalStatus =
  | "allegation"
  | "investigation"
  | "charge"
  | "trial"
  | "conviction"
  | "acquittal"
  | "case_dismissed"
  | "pending"
  | "official_inquiry"
  | "investigative_journalism_report"
  | "mixed"
  | "civil_settlement"
  | "closed"
  | "settled_no_criminal_reference"
  | "reference_withdrawal_sought";

export type ConfidenceLevel = "high" | "medium" | "low";

export interface FinancialLossEstimate {
  value?: number | null;
  currency?: string | null;
  confidence?: string | null;
}

export interface ScandalListItem {
  id: string;
  public_id: string;
  title: string;
  summary: string;
  start_date: string;
  end_date?: string | null;
  province?: string | null;
  city?: string | null;
  latitude?: number | null;
  longitude?: number | null;
  institution?: string | null;
  category: string;
  sector?: string | null;
  amount_pkr?: number | null;
  amount_usd?: number | null;
  amount_notes?: string | null;
  current_legal_status: LegalStatus;
  confidence_score: ConfidenceLevel;
  case_type?: string | null;
  tags?: string[];
  legal_outcome?: string | null;
  source_count: number;
  updated_at?: string | null;
}

export interface Source {
  id: string;
  title: string;
  url: string;
  publisher: string;
  source_type: string;
  published_date?: string | null;
  quote_or_claim?: string | null;
  is_primary: boolean;
}

export interface TimelineEvent {
  id: string;
  event_date: string;
  title: string;
  description?: string | null;
  status_at_event?: LegalStatus | null;
  source_url?: string | null;
}

export interface ScandalDetail extends ScandalListItem {
  government_department?: string | null;
  court_name?: string | null;
  case_number?: string | null;
  related_legislation?: string[] | null;
  financial_loss_estimate?: FinancialLossEstimate | null;
  last_verified?: string | null;
  sources: Source[];
  timeline: TimelineEvent[];
  documents: { id: string; title: string; document_type?: string | null; url?: string | null }[];
  individuals: {
    id: string;
    full_name: string;
    political_party?: string | null;
    position_held?: string | null;
    role_description?: string | null;
  }[];
  institutions: {
    id: string;
    name: string;
    type?: string | null;
    relationship?: string | null;
  }[];
  related_scandal_ids: string[];
  status_label: string;
  disclaimer: string;
}

export interface DashboardStats {
  total_scandals: number;
  total_estimated_pkr: number;
  total_estimated_usd: number;
  by_year: { year: number; count: number }[];
  by_province: { province: string; count: number }[];
  by_institution: { institution: string; count: number }[];
  by_category: { category: string; count: number }[];
  by_status: { status: string; count: number }[];
  by_sector: { sector: string; count: number }[];
  by_case_type?: { case_type: string; count: number }[];
  by_party: { party: string; count: number }[];
  conviction_stats: {
    convictions: number;
    acquittals: number;
    dismissed: number;
    resolved: number;
    conviction_rate: number | null;
    note: string;
  };
  latest: ScandalListItem[];
  disclaimer: string;
}

export interface PaginatedScandals {
  items: ScandalListItem[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export const DISCLAIMER =
  "This project aggregates publicly available information from reputable and official sources for research, transparency, and educational purposes. Inclusion in the database does not imply guilt. Users should consult the cited primary sources and court records for authoritative information.";

export const STATUS_LABELS: Record<LegalStatus, string> = {
  allegation: "Alleged",
  investigation: "Under Investigation",
  charge: "Charged",
  trial: "On Trial",
  conviction: "Convicted",
  acquittal: "Acquitted",
  case_dismissed: "Case Dismissed",
  pending: "Pending",
  official_inquiry: "Official Inquiry",
  investigative_journalism_report: "Investigative Journalism Report",
  mixed: "Mixed Outcomes",
  civil_settlement: "Civil Settlement",
  closed: "Closed",
  settled_no_criminal_reference: "Settled (No Criminal Reference)",
  reference_withdrawal_sought: "Reference Withdrawal Sought",
};
