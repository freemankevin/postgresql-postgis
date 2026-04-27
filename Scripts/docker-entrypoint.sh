#!/usr/bin/env bash
set -e

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
DEFAULT_SHARED_PRELOAD_LIBRARIES="${POSTGRES_SHARED_PRELOAD_LIBRARIES:-pg_stat_statements}"
DEFAULT_PG_STAT_STATEMENTS_TRACK="${POSTGRES_PG_STAT_STATEMENTS_TRACK:-all}"
DEFAULT_PG_STAT_STATEMENTS_MAX="${POSTGRES_PG_STAT_STATEMENTS_MAX:-10000}"

if [ "$1" = 'postgres' ]; then
    has_shared_preload=false
    has_pgss_track=false
    has_pgss_max=false
    
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
fi

exec /usr/local/bin/docker-entrypoint.sh "$@"