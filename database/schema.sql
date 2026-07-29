-- Pakistan Public Corruption Atlas (1960–2026)
-- PostgreSQL schema — OSINT research / journalism only
-- Inclusion does NOT imply guilt. Allegations ≠ facts.

CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TYPE legal_status AS ENUM (
  'allegation',
  'investigation',
  'charge',
  'trial',
  'conviction',
  'acquittal',
  'case_dismissed',
  'pending',
  'official_inquiry',
  'investigative_journalism_report',
  'mixed',
  'civil_settlement',
  'closed',
  'settled_no_criminal_reference',
  'reference_withdrawal_sought'
);

CREATE TYPE confidence_level AS ENUM ('high', 'medium', 'low');

CREATE TYPE scandal_category AS ENUM (
  'procurement',
  'money_laundering',
  'bribery',
  'kickbacks',
  'land_scam',
  'tax_fraud',
  'state_asset_misuse',
  'election_finance',
  'public_fund_embezzlement',
  'ghost_employees',
  'illegal_contracts',
  'infrastructure_fraud',
  'customs',
  'police_corruption',
  'judicial_misconduct',
  'military_procurement',
  'state_owned_enterprises',
  'misuse_of_authority'
);

CREATE TABLE scandals (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  public_id         VARCHAR(32) UNIQUE NOT NULL, -- e.g. PPCA-2008-0042
  title             VARCHAR(500) NOT NULL,
  summary           TEXT NOT NULL,
  start_date        DATE NOT NULL,
  end_date          DATE,
  province          VARCHAR(100),
  city              VARCHAR(100),
  latitude          DOUBLE PRECISION,
  longitude         DOUBLE PRECISION,
  institution       VARCHAR(300),
  government_department VARCHAR(300),
  category          scandal_category NOT NULL,
  sector            VARCHAR(200),
  amount_pkr        NUMERIC(20, 2),
  amount_usd        NUMERIC(20, 2),
  amount_notes      TEXT, -- e.g. "estimated", "alleged", "as per NAB reference"
  current_legal_status legal_status NOT NULL,
  court_name        VARCHAR(300),
  case_number       VARCHAR(200),
  related_legislation TEXT[],
  confidence_score  confidence_level NOT NULL DEFAULT 'medium',
  case_type         VARCHAR(100),
  tags              JSONB DEFAULT '[]'::jsonb,
  financial_loss_estimate JSONB,
  legal_outcome     VARCHAR(300),
  last_verified     DATE,
  content_hash      VARCHAR(64), -- for deduplication
  is_published      BOOLEAN NOT NULL DEFAULT TRUE, -- drafts never exposed on public API
  deleted_at        TIMESTAMPTZ, -- soft delete; public API excludes non-null
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT scandals_date_range CHECK (
    end_date IS NULL OR end_date >= start_date
  ),
  CONSTRAINT scandals_year_window CHECK (
    start_date >= '1960-01-01' AND start_date <= '2026-12-31'
  )
);

CREATE TABLE individuals (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  full_name         VARCHAR(300) NOT NULL,
  aliases           TEXT[],
  political_party   VARCHAR(200), -- only if publicly documented
  notes             TEXT,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE scandal_individuals (
  scandal_id        UUID NOT NULL REFERENCES scandals(id) ON DELETE CASCADE,
  individual_id     UUID NOT NULL REFERENCES individuals(id) ON DELETE CASCADE,
  position_held     VARCHAR(300),
  role_description  TEXT,
  PRIMARY KEY (scandal_id, individual_id)
);

CREATE TABLE institutions (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name              VARCHAR(300) NOT NULL UNIQUE,
  type              VARCHAR(100), -- ministry, SOE, regulator, etc.
  province          VARCHAR(100),
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE scandal_institutions (
  scandal_id        UUID NOT NULL REFERENCES scandals(id) ON DELETE CASCADE,
  institution_id    UUID NOT NULL REFERENCES institutions(id) ON DELETE CASCADE,
  relationship      VARCHAR(100), -- primary, related, investigating
  PRIMARY KEY (scandal_id, institution_id)
);

CREATE TABLE timeline_events (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  scandal_id        UUID NOT NULL REFERENCES scandals(id) ON DELETE CASCADE,
  event_date        DATE NOT NULL,
  title             VARCHAR(500) NOT NULL,
  description       TEXT,
  status_at_event   legal_status,
  source_url        TEXT,
  sort_order        INT NOT NULL DEFAULT 0
);

CREATE TABLE sources (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  scandal_id        UUID NOT NULL REFERENCES scandals(id) ON DELETE CASCADE,
  title             VARCHAR(500) NOT NULL,
  url               TEXT NOT NULL,
  publisher         VARCHAR(300) NOT NULL,
  source_type       VARCHAR(100) NOT NULL, -- government, court, newspaper, intl_org, academic
  published_date    DATE,
  accessed_date     DATE NOT NULL DEFAULT CURRENT_DATE,
  quote_or_claim    TEXT, -- the specific claim this source supports
  is_primary        BOOLEAN NOT NULL DEFAULT FALSE,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE supporting_documents (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  scandal_id        UUID NOT NULL REFERENCES scandals(id) ON DELETE CASCADE,
  title             VARCHAR(500) NOT NULL,
  document_type     VARCHAR(100), -- judgment, audit_report, gazette, nab_reference
  url               TEXT,
  file_path         TEXT,
  published_date    DATE,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE related_scandals (
  scandal_id        UUID NOT NULL REFERENCES scandals(id) ON DELETE CASCADE,
  related_id        UUID NOT NULL REFERENCES scandals(id) ON DELETE CASCADE,
  relationship      VARCHAR(100), -- same_institution, same_individuals, related_procurement
  PRIMARY KEY (scandal_id, related_id),
  CONSTRAINT no_self_relation CHECK (scandal_id <> related_id)
);

CREATE TABLE entity_links (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  source_type       VARCHAR(50) NOT NULL, -- individual, institution, scandal
  source_id         UUID NOT NULL,
  target_type       VARCHAR(50) NOT NULL,
  target_id         UUID NOT NULL,
  link_type         VARCHAR(100) NOT NULL,
  amount_pkr        NUMERIC(20, 2),
  notes             TEXT
);

CREATE TABLE scrape_runs (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  source_name       VARCHAR(200) NOT NULL,
  started_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  finished_at       TIMESTAMPTZ,
  status            VARCHAR(50) NOT NULL DEFAULT 'running',
  records_found     INT DEFAULT 0,
  records_inserted  INT DEFAULT 0,
  records_updated   INT DEFAULT 0,
  errors            JSONB DEFAULT '[]'::jsonb,
  log_path          TEXT
);

CREATE TABLE source_cache (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  url               TEXT UNIQUE NOT NULL,
  content_hash      VARCHAR(64),
  raw_content       TEXT,
  fetched_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  expires_at        TIMESTAMPTZ
);

-- Indexes
CREATE INDEX idx_scandals_province ON scandals(province);
CREATE INDEX idx_scandals_category ON scandals(category);
CREATE INDEX idx_scandals_status ON scandals(current_legal_status);
CREATE INDEX idx_scandals_start_date ON scandals(start_date);
CREATE INDEX idx_scandals_institution ON scandals(institution);
CREATE INDEX idx_scandals_amount_pkr ON scandals(amount_pkr);
CREATE INDEX idx_scandals_published ON scandals(is_published) WHERE deleted_at IS NULL;
CREATE INDEX idx_sources_scandal ON sources(scandal_id);
CREATE INDEX idx_timeline_scandal ON timeline_events(scandal_id, event_date);
CREATE INDEX idx_individuals_name ON individuals(full_name);
CREATE INDEX idx_scrape_runs_source ON scrape_runs(source_name, started_at DESC);

-- Full-text search (PostgreSQL; Meilisearch/ES can mirror this)
CREATE INDEX idx_scandals_fts ON scandals
  USING GIN (to_tsvector('english', coalesce(title,'') || ' ' || coalesce(summary,'') || ' ' || coalesce(institution,'')));

-- Updated_at trigger
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER scandals_updated_at
  BEFORE UPDATE ON scandals
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- View: scandals with source counts (verification readiness)
CREATE OR REPLACE VIEW scandal_verification AS
SELECT
  s.id,
  s.public_id,
  s.title,
  s.confidence_score,
  s.current_legal_status,
  COUNT(DISTINCT src.id) AS source_count,
  COUNT(DISTINCT CASE WHEN src.is_primary THEN src.id END) AS primary_source_count,
  CASE
    WHEN COUNT(DISTINCT src.id) >= 2 THEN TRUE
    ELSE FALSE
  END AS meets_min_sources
FROM scandals s
LEFT JOIN sources src ON src.scandal_id = s.id
GROUP BY s.id;

-- Security / ops audit sink (optional; app also emits structured logs)
CREATE TABLE IF NOT EXISTS security_events (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  event_type        VARCHAR(100) NOT NULL,
  client_ip_hash    VARCHAR(64),
  path              TEXT,
  status_code       INT,
  request_id        VARCHAR(64),
  details           JSONB DEFAULT '{}'::jsonb,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_security_events_type_time ON security_events(event_type, created_at DESC);
