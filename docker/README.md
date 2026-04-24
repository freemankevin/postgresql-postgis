# PostgreSQL PostGIS Docker Image

## Built-in Features

- Pre-installed PostGIS 3 extensions
- Auto-enabled extensions on first startup
- Default `pg_stat_statements` configuration

## Default Configuration

The image includes default PostgreSQL parameters:

- `shared_preload_libraries=pg_stat_statements`
- `pg_stat_statements.track=all`
- `pg_stat_statements.max=10000`

## Override Default Configuration

### Method 1: Environment Variables

```yaml
environment:
  - POSTGRES_SHARED_PRELOAD_LIBRARIES=pg_stat_statements,auto_explain
  - POSTGRES_PG_STAT_STATEMENTS_TRACK=top
  - POSTGRES_PG_STAT_STATEMENTS_MAX=5000
```

### Method 2: Command Arguments

```yaml
command: >
  postgres
  -c shared_preload_libraries=pg_stat_statements,pgaudit
  -c pg_stat_statements.track=top
  -c pg_stat_statements.max=5000
```

### Method 3: Additional PostgreSQL Parameters

```yaml
command: >
  postgres
  -c max_connections=200
  -c shared_buffers=256MB
```

## Custom Initialization Scripts

Mount additional scripts to `/docker-entrypoint-initdb.d/`:

```yaml
volumes:
  - ./init-scripts:/docker-entrypoint-initdb.d:ro
```