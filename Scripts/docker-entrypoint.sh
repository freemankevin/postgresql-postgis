#!/usr/bin/env bash
set -e

# Load log formatter functions
source /usr/local/bin/pg-log-formatter.sh 2>/dev/null || true

# Parse multiple databases from POSTGRES_DB (comma-separated)
if [ -n "$POSTGRES_DB" ] && [[ "$POSTGRES_DB" == *","* ]]; then
    # Split databases by comma
    dbs=(${POSTGRES_DB//,/ })
    first_db="${dbs[0]}"
    extra_dbs="${dbs[1]}"
    
    # Build extra databases list (skip first)
    for i in "${dbs[@]:2}"; do
        extra_dbs="${extra_dbs},${i}"
    done
    
    # Export for official entrypoint (only first database)
    export POSTGRES_DB="$first_db"
    export POSTGRES_EXTRA_DATABASES="$extra_dbs"
    
    echo "Multiple databases detected: POSTGRES_DB='$first_db', EXTRA_DATABASES='$extra_dbs'"
fi

# Default configuration (can be overridden by user command arguments)
DEFAULT_SHARED_PRELOAD_LIBRARIES="${POSTGRES_SHARED_PRELOAD_LIBRARIES:-pg_stat_statements,pgaudit}"
DEFAULT_PG_STAT_STATEMENTS_TRACK="${POSTGRES_PG_STAT_STATEMENTS_TRACK:-all}"
DEFAULT_PG_STAT_STATEMENTS_MAX="${POSTGRES_PG_STAT_STATEMENTS_MAX:-10000}"

# Audit configuration defaults
DEFAULT_PGAUDIT_LOG="${POSTGRES_PGAUDIT_LOG:-write,ddl}"
DEFAULT_PGAUDIT_LOG_RELATION="${POSTGRES_PGAUDIT_LOG_RELATION:-on}"
DEFAULT_PGAUDIT_LOG_PARAMETER="${POSTGRES_PGAUDIT_LOG_PARAMETER:-on}"

# Log configuration defaults
DEFAULT_LOG_LINE_PREFIX="${POSTGRES_LOG_LINE_PREFIX:-%m [%p] %q%u@%d }"
DEFAULT_LOG_STATEMENT="${POSTGRES_LOG_STATEMENT:-ddl}"
DEFAULT_LOG_MIN_DURATION_STATEMENT="${POSTGRES_LOG_MIN_DURATION_STATEMENT:-1000}"
DEFAULT_LOG_CHECKPOINTS="${POSTGRES_LOG_CHECKPOINTS:-on}"
DEFAULT_LOG_CONNECTIONS="${POSTGRES_LOG_CONNECTIONS:-on}"
DEFAULT_LOG_DISCONNECTIONS="${POSTGRES_LOG_DISCONNECTIONS:-on}"
DEFAULT_LOG_LOCK_WAITS="${POSTGRES_LOG_LOCK_WAITS:-on}"
DEFAULT_LOG_TEMP_FILES="${POSTGRES_LOG_TEMP_FILES:-0}"
DEFAULT_LOG_AUTOCANCEL="${POSTGRES_LOG_AUTOCANCEL:-on}"

if [ "$1" = 'postgres' ]; then
    has_shared_preload=false
    has_pgss_track=false
    has_pgss_max=false
    has_log_prefix=false
    
    for arg in "$@"; do
        case "$arg" in
            shared_preload_libraries=*)
                has_shared_preload=true
                ;;
            pg_stat_statements.track=*)
                has_pgss_track=true
                ;;
            pg_stat_statements.max=*)
                has_pgss_max=true
                ;;
            log_line_prefix=*)
                has_log_prefix=true
                ;;
        esac
    done
    
    set -- "$@"
    
    if [ "$has_shared_preload" = false ]; then
        set -- "$@" -c "shared_preload_libraries=$DEFAULT_SHARED_PRELOAD_LIBRARIES"
    fi
    
    if [ "$has_pgss_track" = false ]; then
        set -- "$@" -c "pg_stat_statements.track=$DEFAULT_PG_STAT_STATEMENTS_TRACK"
    fi
    
    if [ "$has_pgss_max" = false ]; then
        set -- "$@" -c "pg_stat_statements.max=$DEFAULT_PG_STAT_STATEMENTS_MAX"
    fi
    
    if [ "$has_log_prefix" = false ]; then
        set -- "$@" -c "log_line_prefix=$DEFAULT_LOG_LINE_PREFIX"
    fi
    
    set -- "$@" \
        -c "log_statement=$DEFAULT_LOG_STATEMENT" \
        -c "log_min_duration_statement=$DEFAULT_LOG_MIN_DURATION_STATEMENT" \
        -c "log_checkpoints=$DEFAULT_LOG_CHECKPOINTS" \
        -c "log_connections=$DEFAULT_LOG_CONNECTIONS" \
        -c "log_disconnections=$DEFAULT_LOG_DISCONNECTIONS" \
        -c "log_lock_waits=$DEFAULT_LOG_LOCK_WAITS" \
        -c "log_temp_files=$DEFAULT_LOG_TEMP_FILES" \
        -c "pgaudit.log=$DEFAULT_PGAUDIT_LOG" \
        -c "pgaudit.log_relation=$DEFAULT_PGAUDIT_LOG_RELATION" \
        -c "pgaudit.log_parameter=$DEFAULT_PGAUDIT_LOG_PARAMETER"
fi

if [ "${POSTGRES_COLORIZE_LOGS:-true}" = "true" ] && [ "$1" = 'postgres' ]; then
    exec /usr/local/bin/docker-entrypoint.sh "$@" 2>&1 | colorize_log
else
    exec /usr/local/bin/docker-entrypoint.sh "$@"
fi