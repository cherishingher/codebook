#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="/opt/codebook"
STORAGE_ROOT="/Volumes/AttendanceData/storage"

mkdir -p "$APP_ROOT"
mkdir -p "$STORAGE_ROOT/backups" "$STORAGE_ROOT/snapshots" "$STORAGE_ROOT/enrollments"
mkdir -p "$STORAGE_ROOT/exports" "$STORAGE_ROOT/logs"

echo "Install Python dependencies inside backend/ and camera-agent/ virtualenvs."
echo "Copy launchd plist files after editing APP_ROOT and STORAGE_ROOT for this Mac."

