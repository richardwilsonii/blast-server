PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS accounts (
  id INTEGER PRIMARY KEY,
  account_kind TEXT NOT NULL DEFAULT 'master'
    CHECK(account_kind IN ('master','slave','other')),
  parent_account_id INTEGER REFERENCES accounts(id),
  wallet_mode TEXT NOT NULL DEFAULT 'individual'
    CHECK(wallet_mode IN ('individual','shared_master','hybrid')),
  status TEXT NOT NULL DEFAULT 'active'
    CHECK(status IN ('active','inactive','anonymized')),
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT,
  anonymized_at TEXT
);

CREATE TABLE IF NOT EXISTS account_links (
  id INTEGER PRIMARY KEY,
  parent_account_id INTEGER NOT NULL REFERENCES accounts(id),
  child_account_id INTEGER NOT NULL REFERENCES accounts(id),
  relationship_type TEXT NOT NULL DEFAULT 'family'
    CHECK(relationship_type IN ('family','guardian','event','other')),
  active INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0,1)),
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  ended_at TEXT,
  UNIQUE(parent_account_id, child_account_id, relationship_type)
);

CREATE TABLE IF NOT EXISTS players (
  id INTEGER PRIMARY KEY,
  account_id INTEGER NOT NULL REFERENCES accounts(id),
  first_name TEXT NOT NULL,
  last_name TEXT NOT NULL,
  nickname TEXT NOT NULL,
  nickname_auto_generated INTEGER NOT NULL DEFAULT 0 CHECK(nickname_auto_generated IN (0,1)),
  nickname_source TEXT NOT NULL DEFAULT 'chosen'
    CHECK(nickname_source IN ('chosen','generated','staff')),
  email TEXT,
  phone TEXT,
  is_minor INTEGER NOT NULL DEFAULT 0 CHECK(is_minor IN (0,1)),
  guardian_account_id INTEGER REFERENCES accounts(id),
  status TEXT NOT NULL DEFAULT 'active'
    CHECK(status IN ('active','inactive','anonymized')),
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT,
  anonymized_at TEXT,
  CHECK(email IS NOT NULL OR phone IS NOT NULL)
);

CREATE TABLE IF NOT EXISTS wristbands (
  id INTEGER PRIMARY KEY,
  uid TEXT NOT NULL UNIQUE,
  status TEXT NOT NULL DEFAULT 'unassigned'
    CHECK(status IN ('unassigned','active','lost','damaged','retired')),
  assigned_player_id INTEGER REFERENCES players(id),
  assigned_account_id INTEGER REFERENCES accounts(id),
  assigned_at TEXT,
  deactivated_at TEXT,
  notes TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS wristband_events (
  id INTEGER PRIMARY KEY,
  wristband_id INTEGER NOT NULL REFERENCES wristbands(id),
  event_type TEXT NOT NULL
    CHECK(event_type IN ('created','assigned','replaced','lost','damaged','retired','reactivated')),
  old_player_id INTEGER REFERENCES players(id),
  new_player_id INTEGER REFERENCES players(id),
  old_account_id INTEGER REFERENCES accounts(id),
  new_account_id INTEGER REFERENCES accounts(id),
  actor_user_id INTEGER REFERENCES admin_users(id),
  reason TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS nickname_words (
  id INTEGER PRIMARY KEY,
  letter TEXT NOT NULL,
  word_position INTEGER NOT NULL CHECK(word_position IN (1,2)),
  word TEXT NOT NULL,
  active INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0,1)),
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  UNIQUE(letter, word_position, word)
);

CREATE INDEX IF NOT EXISTS idx_accounts_parent
ON accounts(parent_account_id);

CREATE INDEX IF NOT EXISTS idx_players_account
ON players(account_id);

CREATE INDEX IF NOT EXISTS idx_players_name
ON players(last_name, first_name);

CREATE INDEX IF NOT EXISTS idx_players_nickname
ON players(nickname);

CREATE INDEX IF NOT EXISTS idx_wristbands_uid
ON wristbands(uid);

CREATE INDEX IF NOT EXISTS idx_wristbands_assigned_player
ON wristbands(assigned_player_id);

INSERT OR IGNORE INTO schema_migrations (version, name)
VALUES ('004', 'identity');
