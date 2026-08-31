#!/usr/bin/env bash
set -euo pipefail

DB="$HOME/bca/db/bca.sqlite"

echo "=== BCA DB Status ==="
echo "DB: $DB"
echo

echo "=== Integrity ==="
sqlite3 "$DB" "PRAGMA foreign_key_check; PRAGMA integrity_check;"
echo

echo "=== Migrations ==="
sqlite3 "$DB" "
SELECT version || ' | ' || name || ' | ' || applied_at
FROM schema_migrations
ORDER BY version;
"
echo

echo "=== Core Counts ==="
sqlite3 "$DB" "
SELECT 'accounts', COUNT(*) FROM accounts
UNION ALL SELECT 'players', COUNT(*) FROM players
UNION ALL SELECT 'wristbands', COUNT(*) FROM wristbands
UNION ALL SELECT 'wallets', COUNT(*) FROM wallets
UNION ALL SELECT 'credit_transactions', COUNT(*) FROM credit_transactions
UNION ALL SELECT 'games', COUNT(*) FROM games
UNION ALL SELECT 'devices', COUNT(*) FROM devices
UNION ALL SELECT 'scanners', COUNT(*) FROM scanners
UNION ALL SELECT 'admin_users', COUNT(*) FROM admin_users
UNION ALL SELECT 'backup_runs', COUNT(*) FROM backup_runs;
"
echo

echo "=== Last Backup ==="
sqlite3 "$DB" "
SELECT id, backup_type, status, file_path, completed_at
FROM backup_runs
ORDER BY id DESC
LIMIT 1;
"
