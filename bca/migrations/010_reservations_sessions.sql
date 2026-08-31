PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS scan_events (
  id INTEGER PRIMARY KEY,
  scanner_id INTEGER REFERENCES scanners(id),
  uid TEXT NOT NULL,
  wristband_id INTEGER REFERENCES wristbands(id),
  player_id INTEGER REFERENCES players(id),
  game_id INTEGER REFERENCES games(id),
  scan_context TEXT NOT NULL
    CHECK(scan_context IN ('front_desk','door','start','admin','unknown')),
  accepted INTEGER NOT NULL DEFAULT 0 CHECK(accepted IN (0,1)),
  rejection_code TEXT,
  reservation_id INTEGER,
  session_id INTEGER,
  raw_payload_json TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS reservations (
  id INTEGER PRIMARY KEY,
  game_id INTEGER NOT NULL REFERENCES games(id),
  status TEXT NOT NULL DEFAULT 'pending'
    CHECK(status IN ('pending','confirmed','canceled','expired','converted')),
  reserved_at TEXT NOT NULL DEFAULT (datetime('now')),
  expires_at TEXT NOT NULL,
  canceled_at TEXT,
  canceled_reason TEXT,
  replaced_by_reservation_id INTEGER REFERENCES reservations(id),
  completion_method TEXT NOT NULL DEFAULT 'timer',
  credit_hold_behavior TEXT NOT NULL DEFAULT 'none',
  expected_player_count INTEGER,
  metadata_json TEXT
);

CREATE TABLE IF NOT EXISTS reservation_players (
  id INTEGER PRIMARY KEY,
  reservation_id INTEGER NOT NULL REFERENCES reservations(id),
  player_id INTEGER NOT NULL REFERENCES players(id),
  wallet_id INTEGER REFERENCES wallets(id),
  outside_scan_event_id INTEGER REFERENCES scan_events(id),
  player_status TEXT NOT NULL DEFAULT 'active'
    CHECK(player_status IN ('active','canceled','replaced','no_show')),
  active INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0,1)),
  joined_at TEXT NOT NULL DEFAULT (datetime('now')),
  UNIQUE(reservation_id, player_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_one_active_reservation_per_player
ON reservation_players(player_id)
WHERE active = 1;

CREATE TABLE IF NOT EXISTS start_attempts (
  id INTEGER PRIMARY KEY,
  reservation_id INTEGER NOT NULL REFERENCES reservations(id),
  game_id INTEGER NOT NULL REFERENCES games(id),
  status TEXT NOT NULL DEFAULT 'pending'
    CHECK(status IN ('pending','approved','rejected','expired')),
  started_at TEXT NOT NULL DEFAULT (datetime('now')),
  ended_at TEXT,
  rejection_code TEXT,
  message TEXT
);

CREATE TABLE IF NOT EXISTS start_attempt_players (
  id INTEGER PRIMARY KEY,
  start_attempt_id INTEGER NOT NULL REFERENCES start_attempts(id),
  player_id INTEGER NOT NULL REFERENCES players(id),
  scan_event_id INTEGER REFERENCES scan_events(id),
  scanned_at TEXT NOT NULL DEFAULT (datetime('now')),
  UNIQUE(start_attempt_id, player_id)
);

CREATE TABLE IF NOT EXISTS game_sessions (
  id INTEGER PRIMARY KEY,
  reservation_id INTEGER NOT NULL UNIQUE REFERENCES reservations(id),
  game_id INTEGER NOT NULL REFERENCES games(id),
  status TEXT NOT NULL DEFAULT 'starting'
    CHECK(status IN ('starting','running','completed','failed','aborted')),
  session_type TEXT NOT NULL DEFAULT 'normal'
    CHECK(session_type IN ('normal','test','admin')),
  started_at TEXT NOT NULL DEFAULT (datetime('now')),
  ended_at TEXT,
  time_limit_sec INTEGER NOT NULL,
  completion_reason TEXT,
  total_credit_cost INTEGER NOT NULL DEFAULT 0,
  start_request_id TEXT UNIQUE,
  metadata_json TEXT
);

CREATE TABLE IF NOT EXISTS session_players (
  id INTEGER PRIMARY KEY,
  session_id INTEGER NOT NULL REFERENCES game_sessions(id),
  player_id INTEGER NOT NULL REFERENCES players(id),
  wallet_id INTEGER REFERENCES wallets(id),
  credits_charged INTEGER NOT NULL DEFAULT 0,
  UNIQUE(session_id, player_id)
);

CREATE TABLE IF NOT EXISTS session_credit_lines (
  id INTEGER PRIMARY KEY,
  session_id INTEGER NOT NULL REFERENCES game_sessions(id),
  player_id INTEGER NOT NULL REFERENCES players(id),
  wallet_id INTEGER NOT NULL REFERENCES wallets(id),
  credit_transaction_id INTEGER NOT NULL UNIQUE REFERENCES credit_transactions(id),
  amount_credits INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS session_events (
  id INTEGER PRIMARY KEY,
  session_id INTEGER NOT NULL REFERENCES game_sessions(id),
  event_type TEXT NOT NULL,
  device_id INTEGER REFERENCES devices(id),
  payload_json TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_scan_events_uid_created
ON scan_events(uid, created_at);

CREATE INDEX IF NOT EXISTS idx_scan_events_player_created
ON scan_events(player_id, created_at);

CREATE INDEX IF NOT EXISTS idx_reservations_game_status
ON reservations(game_id, status);

CREATE INDEX IF NOT EXISTS idx_start_attempts_reservation_status
ON start_attempts(reservation_id, status);

CREATE INDEX IF NOT EXISTS idx_game_sessions_game_status
ON game_sessions(game_id, status);

CREATE INDEX IF NOT EXISTS idx_session_events_session_created
ON session_events(session_id, created_at);

INSERT OR IGNORE INTO schema_migrations (version, name)
VALUES ('010', 'reservations_sessions');
