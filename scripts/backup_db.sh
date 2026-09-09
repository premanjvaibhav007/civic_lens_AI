#!/usr/bin/env bash
# CivicLens AI - Database Backup Utility (PostgreSQL & SQLite)
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-./backups}"
mkdir -p "$BACKUP_DIR"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

if [ -n "${DATABASE_URL:-}" ] && [[ "$DATABASE_URL" == postgres* ]]; then
    echo "=== Backing up PostgreSQL database ==="
    BACKUP_FILE="$BACKUP_DIR/civiclens_pg_${TIMESTAMP}.sql.gz"
    # Extract connection components or use docker exec
    if docker ps | grep -q civiclens-postgres; then
        docker exec -t civiclens-postgres pg_dump -U civicadmin civiclens | gzip > "$BACKUP_FILE"
    else
        pg_dump "$DATABASE_URL" | gzip > "$BACKUP_FILE"
    fi
    echo "Backup completed successfully -> $BACKUP_FILE"
else
    echo "=== Backing up SQLite database ==="
    SQLITE_DB="${SQLITE_DB:-./civiclens.db}"
    if [ -f "$SQLITE_DB" ]; then
        BACKUP_FILE="$BACKUP_DIR/civiclens_sqlite_${TIMESTAMP}.db"
        sqlite3 "$SQLITE_DB" ".backup '$BACKUP_FILE'" || cp "$SQLITE_DB" "$BACKUP_FILE"
        echo "Backup completed successfully -> $BACKUP_FILE"
    else
        echo "Error: Database file $SQLITE_DB not found!" >&2
        exit 1
    fi
fi
