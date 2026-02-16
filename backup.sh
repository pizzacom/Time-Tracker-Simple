#!/bin/bash
# ===========================
# ZeitTracker Database Backup Script
# ===========================
# Usage: ./backup.sh [retention_days]
# Default retention: 30 days

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR="${SCRIPT_DIR}/backups"
RETENTION_DAYS="${1:-30}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/zeittracker_${TIMESTAMP}.sql.gz"

# Load environment variables
if [ -f "${SCRIPT_DIR}/.env" ]; then
    export $(grep -v '^#' "${SCRIPT_DIR}/.env" | xargs)
fi

DB_USER="${POSTGRES_USER:-zeittracker}"
DB_NAME="${POSTGRES_DB:-zeittracker}"
DB_CONTAINER="time-tracker-simple-db-1"

# Create backup directory
mkdir -p "${BACKUP_DIR}"

echo "=== ZeitTracker Backup ==="
echo "Date: $(date)"
echo "Target: ${BACKUP_FILE}"

# Run pg_dump inside the container and compress
docker exec "${DB_CONTAINER}" pg_dump -U "${DB_USER}" "${DB_NAME}" | gzip > "${BACKUP_FILE}"

if [ $? -eq 0 ]; then
    SIZE=$(du -h "${BACKUP_FILE}" | cut -f1)
    echo "✓ Backup created successfully (${SIZE})"
else
    echo "✗ Backup failed!"
    exit 1
fi

# Remove old backups
DELETED=$(find "${BACKUP_DIR}" -name "zeittracker_*.sql.gz" -mtime "+${RETENTION_DAYS}" -print -delete | wc -l)
if [ "${DELETED}" -gt 0 ]; then
    echo "✓ Removed ${DELETED} backup(s) older than ${RETENTION_DAYS} days"
fi

echo "=== Done ==="

# List current backups
echo ""
echo "Current backups:"
ls -lh "${BACKUP_DIR}"/zeittracker_*.sql.gz 2>/dev/null || echo "  (none)"
