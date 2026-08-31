PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS games (
  id INTEGER PRIMARY KEY,
  game_code TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  public_description TEXT,
  enabled INTEGER NOT NULL DEFAULT 1 CHECK(enabled IN (0,1)),
  display_order INTEGER NOT NULL DEFAULT 0,
  location_code TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT
);

CREATE TABLE IF NOT EXISTS game_configs (
  id INTEGER PRIMARY KEY,
  game_id INTEGER NOT NULL UNIQUE REFERENCES games(id),
  credit_cost INTEGER NOT NULL DEFAULT 1 CHECK(credit_cost >= 0),
  min_players INTEGER NOT NULL DEFAULT 1 CHECK(min_players >= 1),
  max_players INTEGER NOT NULL DEFAULT 1 CHECK(max_players >= min_players),
  time_limit_sec INTEGER NOT NULL DEFAULT 300,
  reservation_timeout_sec INTEGER NOT NULL DEFAULT 300,
  score_type TEXT NOT NULL DEFAULT 'points',
  score_direction TEXT NOT NULL DEFAULT 'high_wins'
    CHECK(score_direction IN ('high_wins','low_wins','custom')),
  score_scope TEXT NOT NULL DEFAULT 'individual'
    CHECK(score_scope IN ('individual','team','both')),
  reservation_completion_method TEXT NOT NULL DEFAULT 'timer',
  reservation_credit_hold_behavior TEXT NOT NULL DEFAULT 'none',
  allows_leaderboard INTEGER NOT NULL DEFAULT 1 CHECK(allows_leaderboard IN (0,1)),
  allows_replay INTEGER NOT NULL DEFAULT 1 CHECK(allows_replay IN (0,1)),
  requires_door_scanner INTEGER NOT NULL DEFAULT 1 CHECK(requires_door_scanner IN (0,1)),
  requires_start_scanner INTEGER NOT NULL DEFAULT 1 CHECK(requires_start_scanner IN (0,1)),
  requires_controller_heartbeat INTEGER NOT NULL DEFAULT 1 CHECK(requires_controller_heartbeat IN (0,1)),
  requires_lock_heartbeat INTEGER NOT NULL DEFAULT 1 CHECK(requires_lock_heartbeat IN (0,1)),
  manual_fault_clear_required INTEGER NOT NULL DEFAULT 1 CHECK(manual_fault_clear_required IN (0,1)),
  metadata_json TEXT
);

CREATE TABLE IF NOT EXISTS game_status (
  id INTEGER PRIMARY KEY,
  game_id INTEGER NOT NULL UNIQUE REFERENCES games(id),
  availability_state TEXT NOT NULL DEFAULT 'offline'
    CHECK(availability_state IN ('available','reserved','running','maintenance','offline','faulted')),
  blocking_fault_id INTEGER,
  current_reservation_id INTEGER,
  current_session_id INTEGER,
  status_message TEXT,
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS game_status_events (
  id INTEGER PRIMARY KEY,
  game_id INTEGER NOT NULL REFERENCES games(id),
  from_state TEXT,
  to_state TEXT NOT NULL,
  reason TEXT,
  source_type TEXT,
  source_id INTEGER,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS devices (
  id INTEGER PRIMARY KEY,
  device_code TEXT NOT NULL UNIQUE,
  device_name TEXT NOT NULL,
  device_type TEXT NOT NULL
    CHECK(device_type IN ('server','mqtt_broker','game_pi','pico_w','scanner','lock_controller','tablet','game_pc','network','other')),
  game_id INTEGER REFERENCES games(id),
  parent_device_id INTEGER REFERENCES devices(id),
  host_device_id INTEGER REFERENCES devices(id),
  required_for_availability INTEGER NOT NULL DEFAULT 0 CHECK(required_for_availability IN (0,1)),
  status TEXT NOT NULL DEFAULT 'offline'
    CHECK(status IN ('online','offline','degraded','faulted','disabled')),
  last_seen_at TEXT,
  heartbeat_interval_sec INTEGER NOT NULL DEFAULT 30,
  offline_threshold_sec INTEGER NOT NULL DEFAULT 90,
  reconnect_grace_sec INTEGER NOT NULL DEFAULT 10,
  manual_fault_clear_required INTEGER NOT NULL DEFAULT 1 CHECK(manual_fault_clear_required IN (0,1)),
  metadata_json TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT
);

CREATE TABLE IF NOT EXISTS scanners (
  id INTEGER PRIMARY KEY,
  device_id INTEGER NOT NULL UNIQUE REFERENCES devices(id),
  game_id INTEGER REFERENCES games(id),
  scanner_type TEXT NOT NULL
    CHECK(scanner_type IN ('front_desk','door','start','admin')),
  scan_point_code TEXT NOT NULL UNIQUE,
  required_for_game INTEGER NOT NULL DEFAULT 0 CHECK(required_for_game IN (0,1)),
  allow_scans_when_offline INTEGER NOT NULL DEFAULT 0 CHECK(allow_scans_when_offline IN (0,1)),
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS door_locks (
  id INTEGER PRIMARY KEY,
  device_id INTEGER NOT NULL UNIQUE REFERENCES devices(id),
  game_id INTEGER REFERENCES games(id),
  lock_code TEXT NOT NULL UNIQUE,
  required_for_game INTEGER NOT NULL DEFAULT 1 CHECK(required_for_game IN (0,1)),
  current_lock_state TEXT NOT NULL DEFAULT 'unknown'
    CHECK(current_lock_state IN ('locked','unlocked','unknown','faulted')),
  emergency_release_seen INTEGER NOT NULL DEFAULT 0 CHECK(emergency_release_seen IN (0,1)),
  last_command_at TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT
);

CREATE TABLE IF NOT EXISTS device_events (
  id INTEGER PRIMARY KEY,
  device_id INTEGER NOT NULL REFERENCES devices(id),
  event_type TEXT NOT NULL,
  from_status TEXT,
  to_status TEXT,
  payload_json TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_games_display_order
ON games(display_order);

CREATE INDEX IF NOT EXISTS idx_game_status_state
ON game_status(availability_state);

CREATE INDEX IF NOT EXISTS idx_devices_game_type
ON devices(game_id, device_type);

CREATE INDEX IF NOT EXISTS idx_devices_status
ON devices(status);

CREATE INDEX IF NOT EXISTS idx_scanners_game_type
ON scanners(game_id, scanner_type);

CREATE INDEX IF NOT EXISTS idx_device_events_device_created
ON device_events(device_id, created_at);

INSERT OR IGNORE INTO devices (
  device_code,
  device_name,
  device_type,
  required_for_availability,
  status,
  heartbeat_interval_sec,
  offline_threshold_sec,
  manual_fault_clear_required
)
VALUES
('blast-server', 'Central Server / blast-server', 'server', 1, 'online', 30, 90, 1),
('mqtt-main', 'Main MQTT Broker', 'mqtt_broker', 1, 'offline', 30, 90, 1),
('frontdesk-scanner-1', 'Front Desk Scanner 1', 'scanner', 0, 'offline', 30, 90, 1);

INSERT OR IGNORE INTO scanners (
  device_id,
  scanner_type,
  scan_point_code,
  required_for_game,
  allow_scans_when_offline
)
SELECT id, 'front_desk', 'frontdesk-scanner-1', 0, 0
FROM devices
WHERE device_code = 'frontdesk-scanner-1';

INSERT OR IGNORE INTO schema_migrations (version, name)
VALUES ('008', 'games_devices');
