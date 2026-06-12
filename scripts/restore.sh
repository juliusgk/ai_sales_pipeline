#!/usr/bin/env bash
# Restore a PostgreSQL backup from S3.
#
# Usage:
#   ./scripts/restore.sh                        # Restores the latest backup
#   ./scripts/restore.sh 2026-06-12_02-00-00   # Restores a specific backup

set -euo pipefail

# ---- Configuration — must match backup.sh ----
S3_BUCKET="your-bucket-name"
DB_CONTAINER="sales_pipeline-db-1"
DB_NAME="sales_pipeline"
DB_USER="sales_user"
# -----------------------------------------------

echo "=== AI Sales Pipeline — Database Restore ==="

# Find the backup to restore
if [ -n "${1:-}" ]; then
    BACKUP_FILE="sales_pipeline_${1}.sql.gz"
else
    echo "No date specified — finding latest backup..."
    BACKUP_FILE=$(aws s3 ls "s3://${S3_BUCKET}/backups/" \
        | sort | tail -1 | awk '{print $4}')
fi

if [ -z "$BACKUP_FILE" ]; then
    echo "ERROR: No backup found in s3://${S3_BUCKET}/backups/"
    exit 1
fi

echo "Restoring from: $BACKUP_FILE"
echo "WARNING: This will overwrite all current data. Press Ctrl+C to cancel."
sleep 5

# Download from S3
LOCAL_FILE="/tmp/${BACKUP_FILE}"
aws s3 cp "s3://${S3_BUCKET}/backups/${BACKUP_FILE}" "$LOCAL_FILE"

# Restore
gunzip -c "$LOCAL_FILE" | docker exec -i "$DB_CONTAINER" \
    psql -U "$DB_USER" "$DB_NAME"

rm "$LOCAL_FILE"

echo "Restore complete from $BACKUP_FILE"
