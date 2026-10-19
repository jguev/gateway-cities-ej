-- 001_schemas.sql
-- Layered schemas and a read-only role that can see only published data
-- Safe to run repeatedly.

CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS analytics;
CREATE SCHEMA IF NOT EXISTS published;

DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'map_reader') THEN
        CREATE ROLE map_reader LOGIN;
    END IF;
END
$$;

-- Lock the private layers
REVOKE ALL ON SCHEMA raw, staging, analytics FROM PUBLIC;

-- Read-only access to published
GRANT USAGE ON SCHEMA published TO map_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA published TO map_reader;
ALTER DEFAULT PRIVILEGES IN SCHEMA published
    GRANT SELECT ON TABLES TO map_reader;