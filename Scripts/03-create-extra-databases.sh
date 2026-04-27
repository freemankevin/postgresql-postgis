#!/bin/bash
set -e

# Create extra databases if POSTGRES_EXTRA_DATABASES is set
if [ -n "$POSTGRES_EXTRA_DATABASES" ]; then
    echo "Creating extra databases: $POSTGRES_EXTRA_DATABASES"
    
    for db in ${POSTGRES_EXTRA_DATABASES//,/ }; do
        echo "Creating database: $db"
        psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname postgres <<-EOSQL
            CREATE DATABASE "$db";
EOSQL
        echo "Database $db created successfully"
    done
    
    echo "All extra databases created"
fi