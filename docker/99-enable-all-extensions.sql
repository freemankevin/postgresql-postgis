-- ============================================
-- PostgreSQL Extensions Initialization Script
-- ============================================

-- 1. Basic types/functions (no dependencies)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;
CREATE EXTENSION IF NOT EXISTS unaccent;

-- 2. Storage/index extensions
CREATE EXTENSION IF NOT EXISTS hstore;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS btree_gin;
CREATE EXTENSION IF NOT EXISTS btree_gist;
CREATE EXTENSION IF NOT EXISTS intarray;

-- 3. PostGIS core
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
CREATE EXTENSION IF NOT EXISTS postgis_raster;

-- 4. PostGIS advanced (optional, may require additional dependencies)
-- CREATE EXTENSION IF NOT EXISTS postgis_sfcgal;
CREATE EXTENSION IF NOT EXISTS postgis_tiger_geocoder;
CREATE EXTENSION IF NOT EXISTS address_standardizer;
CREATE EXTENSION IF NOT EXISTS address_standardizer_data_us;

-- 5. Cross-database access
CREATE EXTENSION IF NOT EXISTS dblink;
CREATE EXTENSION IF NOT EXISTS postgres_fdw;
CREATE EXTENSION IF NOT EXISTS file_fdw;

-- 6. Monitoring/operations (require shared_preload_libraries)
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
CREATE EXTENSION IF NOT EXISTS pg_buffercache;
CREATE EXTENSION IF NOT EXISTS pg_prewarm;

-- 7. Development/testing tools
CREATE EXTENSION IF NOT EXISTS pg_surgery;
CREATE EXTENSION IF NOT EXISTS pageinspect;
CREATE EXTENSION IF NOT EXISTS amcheck;
CREATE EXTENSION IF NOT EXISTS pgrowlocks;
CREATE EXTENSION IF NOT EXISTS pgstattuple;

-- 8. Crosstab/pivot table functions
CREATE EXTENSION IF NOT EXISTS tablefunc;

-- Verify critical extensions
SELECT extname, extversion FROM pg_extension WHERE extname IN ('postgis', 'pg_trgm', 'uuid-ossp') ORDER BY extname;