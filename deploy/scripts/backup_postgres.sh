#!/usr/bin/env bash
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/Volumes/AttendanceData/storage/backups}"
DATABASE_URL="${DATABASE_URL:-postgresql://codebook:codebook@127.0.0.1:5432/codebook}"
STAMP="$(date +%Y%m%d-%H%M%S)"

mkdir -p "$BACKUP_DIR"
pg_dump "$DATABASE_URL" | gzip > "$BACKUP_DIR/codebook-$STAMP.sql.gz"

