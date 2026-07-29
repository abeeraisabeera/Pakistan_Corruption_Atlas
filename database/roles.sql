-- Least-privilege database roles for Neon / self-hosted Postgres.
-- Run as a superuser / Neon owner AFTER schema.sql.
-- Replace passwords before production. Never commit real passwords.

-- Application role: read published catalog (+ write only if you later grant it)
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'ppca_app') THEN
    CREATE ROLE ppca_app LOGIN PASSWORD 'CHANGE_ME_app_role';
  END IF;
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'ppca_migrator') THEN
    CREATE ROLE ppca_migrator LOGIN PASSWORD 'CHANGE_ME_migrator_role';
  END IF;
END
$$;

-- Revoke broad public access
REVOKE ALL ON SCHEMA public FROM PUBLIC;
GRANT USAGE ON SCHEMA public TO ppca_app, ppca_migrator;

-- Migrator: DDL + DML for schema changes / ingest
GRANT ALL ON ALL TABLES IN SCHEMA public TO ppca_migrator;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO ppca_migrator;
GRANT ALL ON ALL FUNCTIONS IN SCHEMA public TO ppca_migrator;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO ppca_migrator;

-- App: SELECT on research tables; no DROP
GRANT SELECT ON ALL TABLES IN SCHEMA public TO ppca_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO ppca_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO ppca_app;

-- If the API will insert scrape_runs / source_cache, grant narrowly:
-- GRANT INSERT, UPDATE ON scrape_runs, source_cache TO ppca_app;

-- Neon notes:
-- * Enable PITR / backups in the Neon console (automatic backups + restore).
-- * Use DATABASE_URL with sslmode=require (or channel_binding as Neon documents).
-- * Point HF Space DATABASE_URL at the ppca_app connection string for production reads.
-- * Use ppca_migrator only for migrations and verified ingest jobs.
