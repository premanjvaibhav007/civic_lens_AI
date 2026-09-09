#!/usr/bin/env bash
# CivicLens AI - Database Restore Utility
set -euo pipefail

if [ $# -lt 1 ]; then
    echo "Usage: $0 <backup_file_path>" >&2
    exit 1
fi

BACKUP_FILE="$1"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "Error: Backup file $BACKUP_FILE does not exist!" >&2
    exit 1
fi

if [[ "$BACKUP_FILE" == *.sql.gz ]] || [[ "$BACKUP_FILE" == *.sql ]]; then
    echo "=== Restoring PostgreSQL database from $BACKUP_FILE ==="
    if docker ps | grep -q civiclens-postgres; then
        gunzip -c "$BACKUP_FILE" | docker exec -i civiclens-postgres psql -U civicadmin -d civiclens
    else
        gunzip -c "$BACKUP_FILE" | psql "${DATABASE_URL}"
    fi
    echo "Restore completed successfully."
elif [[ "$BACKUP_FILE" == *.db ]]; then
    echo "=== Restoring SQLite database from $BACKUP_FILE ==="
    TARGET_DB="${SQLITE_DB:-./civiclens.db}"
    # Safety backup of current db
    if [ -f "$TARGET_DB" ]; then
        cp "$TARGET_DB" "${TARGET_DB}.pre_restore_bak"
        echo "Created pre-restore safety copy at ${TARGET_DB}.pre_restore_bak"
    fi
    cp "$BACKUP_FILE" "$TARGET_DB"
    echo "Restore completed successfully to $TARGET_DB."
else
    echo "Unrecognized backup file format: $BACKUP_FILE" >&2
    exit 1
fi
