#!/usr/bin/env bash
set -e

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