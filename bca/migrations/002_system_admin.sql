PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS admin_users (
  id INTEGER PRIMARY KEY,
  username TEXT NOT NULL UNIQUE,
  display_name TEXT NOT NULL,
  password_hash TEXT,
  override_pin_hash TEXT,
  active INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0,1)),
  must_change_password INTEGER NOT NULL DEFAULT 1 CHECK(must_change_password IN (0,1)),
  last_login_at TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT
);

CREATE TABLE IF NOT EXISTS roles (
  id INTEGER PRIMARY KEY,
  role_key TEXT NOT NULL UNIQUE,
  role_name TEXT NOT NULL,
  active INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0,1)),
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS user_roles (
  id INTEGER PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES admin_users(id),
  role_id INTEGER NOT NULL REFERENCES roles(id),
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  UNIQUE(user_id, role_id)
);

CREATE TABLE IF NOT EXISTS role_permissions (
  id INTEGER PRIMARY KEY,
  role_id INTEGER NOT NULL REFERENCES roles(id),
  permission_key TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  UNIQUE(role_id, permission_key)
);

CREATE TABLE IF NOT EXISTS system_settings (
  id INTEGER PRIMARY KEY,
  scope TEXT NOT NULL DEFAULT 'global',
  setting_key TEXT NOT NULL,
  value_json TEXT NOT NULL,
  updated_by_user_id INTEGER REFERENCES admin_users(id),
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT,
  UNIQUE(scope, setting_key)
);

CREATE TABLE IF NOT EXISTS audit_log (
  id INTEGER PRIMARY KEY,
  event_type TEXT NOT NULL,
  actor_user_id INTEGER REFERENCES admin_users(id),
  target_type TEXT,
  target_id INTEGER,
  before_json TEXT,
  after_json TEXT,
  reason TEXT,
  request_id TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS alerts (
  id INTEGER PRIMARY KEY,
  severity TEXT NOT NULL CHECK(severity IN ('low','medium','high','critical')),
  status TEXT NOT NULL DEFAULT 'open' CHECK(status IN ('open','acknowledged','resolved','dismissed')),
  source_type TEXT,
  source_id INTEGER,
  game_id INTEGER,
  device_id INTEGER,
  message TEXT NOT NULL,
  acknowledged_by_user_id INTEGER REFERENCES admin_users(id),
  acknowledged_at TEXT,
  resolved_by_user_id INTEGER REFERENCES admin_users(id),
  resolved_at TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS backup_runs (
  id INTEGER PRIMARY KEY,
  backup_type TEXT NOT NULL CHECK(backup_type IN ('local','cloud','restore_test')),
  status TEXT NOT NULL CHECK(status IN ('started','success','failed')),
  file_path TEXT,
  size_bytes INTEGER,
  checksum TEXT,
  error_message TEXT,
  started_at TEXT NOT NULL DEFAULT (datetime('now')),
  completed_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_audit_log_created_at
ON audit_log(created_at);

CREATE INDEX IF NOT EXISTS idx_audit_log_target
ON audit_log(target_type, target_id);

CREATE INDEX IF NOT EXISTS idx_alerts_status_severity_created
ON alerts(status, severity, created_at);

INSERT OR IGNORE INTO schema_migrations (version, name)
VALUES ('002', 'system_admin');
