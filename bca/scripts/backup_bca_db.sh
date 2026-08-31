#!/usr/bin/env bash
set -euo pipefail

DB="$HOME/bca/db/bca.sqlite"
BACKUP_DIR="$HOME/bca/backups"
STAMP="$(date +%Y%m%d_%H%M%S)"
OUT="$BACKUP_DIR/bca_$STAMP.sqlite"

mkdir -p "$BACKUP_DIR"

sqlite3 "$DB" "VACUUM INTO '$OUT';"

SIZE_BYTES="$(stat -c%s "$OUT")"
CHECKSUM="$(sha256sum "$OUT" | awk '{print $1}')"

sqlite3 "$DB" "
INSERT INTO backup_runs (
  backup_type,
  status,
  file_path,
  size_bytes,
  checksum,
  completed_at
)
VALUES (
  'local',
  'success',
  '$OUT',
  $SIZE_BYTES,
  '$CHECKSUM',
  datetime('now')
);
"

echo "Backup created:"
echo "$OUT"
echo "Size: $SIZE_BYTES bytes"
echo "SHA256: $CHECKSUM"
