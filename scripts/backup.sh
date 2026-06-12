#!/usr/bin/env bash
# Daily PostgreSQL backup — dumps the database and uploads to S3.
#
# Setup:
#   1. Install AWS CLI on the VM:  sudo apt-get install -y awscli
#   2. Configure credentials:      aws configure
#   3. Create an S3 bucket:        aws s3 mb s3://your-bucket-name
#   4. Edit the variables below
#   5. Test manually:              ./scripts/backup.sh
#   6. Add to cron (runs at 2am):  crontab -e
#      Add this line:
#      0 2 * * * /path/to/ai_sales_pipeline/scripts/backup.sh >> /var/log/sales_backup.log 2>&1

set -euo pipefail

# ---- Configuration — edit these ----
S3_BUCKET="your-bucket-name"          # e.g. "julius-sales-pipeline-backups"
KEEP_DAYS=30                           # Delete backups older than this
DB_CONTAINER="sales_pipeline-db-1"    # Docker container name (check with: docker ps)
DB_NAME="sales_pipeline"
DB_USER="sales_user"
# ------------------------------------

DATE=$(date +%Y-%m-%d_%H-%M-%S)
BACKUP_FILE="/tmp/sales_pipeline_${DATE}.sql.gz"

echo "[${DATE}] Starting backup..."

# 1. Dump the database and compress it
docker exec "$DB_CONTAINER" \
    pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "$BACKUP_FILE"

echo "[${DATE}] Dump complete: $(du -sh "$BACKUP_FILE" | cut -f1)"

# 2. Upload to S3
aws s3 cp "$BACKUP_FILE" "s3://${S3_BUCKET}/backups/$(basename "$BACKUP_FILE")"

echo "[${DATE}] Uploaded to s3://${S3_BUCKET}/backups/"

# 3. Delete the local temp file
rm "$BACKUP_FILE"

# 4. Remove backups older than KEEP_DAYS from S3
aws s3 ls "s3://${S3_BUCKET}/backups/" | while read -r line; do
    FILE_DATE=$(echo "$line" | awk '{print $1}')
    FILE_NAME=$(echo "$line" | awk '{print $4}')
    if [[ $(date -d "$FILE_DATE" +%s 2>/dev/null || date -j -f "%Y-%m-%d" "$FILE_DATE" +%s) \
          -lt $(date -d "-${KEEP_DAYS} days" +%s 2>/dev/null || date -v-${KEEP_DAYS}d +%s) ]]; then
        aws s3 rm "s3://${S3_BUCKET}/backups/${FILE_NAME}"
        echo "[${DATE}] Deleted old backup: ${FILE_NAME}"
    fi
done

echo "[${DATE}] Backup complete."
