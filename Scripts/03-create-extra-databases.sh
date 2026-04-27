#!/bin/bash
set -e

# Create extra databases if POSTGRES_EXTRA_DATABASES is set
if [ -n "$POSTGRES_EXTRA_DATABASES" ]; then
    echo "Creating extra databases: $POSTGRES_EXTRA_DATABASES"
    
    for db in ${POSTGRES_EXTRA_DATABASES//,/ }; do
        db_exists=$(psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname postgres -tAc "SELECT 1 FROM pg_database WHERE datname='$db'")
        if [ "$db_exists" != "1" ]; then
            echo "Creating database: $db"
            psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname postgres -c "CREATE DATABASE \"$db\""
            echo "Database $db created successfully"
        else
            echo "Database $db already exists, skipping"
        fi
    done
    
    echo "All extra databases created"
fi