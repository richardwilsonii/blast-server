PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS scores (
  id INTEGER PRIMARY KEY,
  session_id INTEGER NOT NULL REFERENCES game_sessions(id),
  game_id INTEGER NOT NULL REFERENCES games(id),
  player_id INTEGER REFERENCES players(id),
  score_scope TEXT NOT NULL CHECK(score_scope IN ('individual','team')),
  score_value_num REAL,
  score_value_text TEXT,
  score_units TEXT,
  score_direction TEXT NOT NULL CHECK(score_direction IN ('high_wins','low_wins','custom')),
  completion_status TEXT,
  leaderboard_eligible INTEGER NOT NULL DEFAULT 1 CHECK(leaderboard_eligible IN (0,1)),
  ineligible_reason TEXT,
  play_date_local TEXT NOT NULL,
  leaderboard_week_start TEXT NOT NULL,
  leaderboard_month_start TEXT NOT NULL,
  metadata_json TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS score_components (
  id INTEGER PRIMARY KEY,
  score_id INTEGER NOT NULL REFERENCES scores(id),
  component_key TEXT NOT NULL,
  value_num REAL,
  value_text TEXT,
  metadata_json TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS leaderboard_cache (
  id INTEGER PRIMARY KEY,
  game_id INTEGER NOT NULL REFERENCES games(id),
  period_type TEXT NOT NULL CHECK(period_type IN ('daily','weekly','monthly','all_time')),
  period_start TEXT,
  period_end TEXT,
  score_id INTEGER NOT NULL REFERENCES scores(id),
  rank INTEGER NOT NULL,
  generated_at TEXT NOT NULL DEFAULT (datetime('now')),
  filter_json TEXT,
  UNIQUE(game_id, period_type, period_start, period_end, score_id)
);

CREATE INDEX IF NOT EXISTS idx_scores_game_eligible_date
ON scores(game_id, leaderboard_eligible, play_date_local);

CREATE INDEX IF NOT EXISTS idx_scores_game_week
ON scores(game_id, leaderboard_week_start);

CREATE INDEX IF NOT EXISTS idx_scores_game_month
ON scores(game_id, leaderboard_month_start);

CREATE INDEX IF NOT EXISTS idx_scores_session
ON scores(session_id);

CREATE INDEX IF NOT EXISTS idx_score_components_score
ON score_components(score_id);

CREATE VIEW IF NOT EXISTS v_public_leaderboard_all_time AS
SELECT
  g.id AS game_id,
  g.game_code,
  g.name AS game_name,
  p.nickname,
  s.score_value_num,
  s.score_value_text,
  s.score_units,
  s.score_direction,
  s.created_at,
  s.id AS score_id
FROM scores s
JOIN games g ON g.id = s.game_id
JOIN game_sessions gs ON gs.id = s.session_id
LEFT JOIN players p ON p.id = s.player_id
WHERE s.leaderboard_eligible = 1
  AND gs.session_type = 'normal';

CREATE VIEW IF NOT EXISTS v_public_leaderboard_weekly AS
SELECT
  g.id AS game_id,
  g.game_code,
  g.name AS game_name,
  p.nickname,
  s.score_value_num,
  s.score_value_text,
  s.score_units,
  s.score_direction,
  s.leaderboard_week_start,
  s.created_at,
  s.id AS score_id
FROM scores s
JOIN games g ON g.id = s.game_id
JOIN game_sessions gs ON gs.id = s.session_id
LEFT JOIN players p ON p.id = s.player_id
WHERE s.leaderboard_eligible = 1
  AND gs.session_type = 'normal';

CREATE VIEW IF NOT EXISTS v_public_leaderboard_monthly AS
SELECT
  g.id AS game_id,
  g.game_code,
  g.name AS game_name,
  p.nickname,
  s.score_value_num,
  s.score_value_text,
  s.score_units,
  s.score_direction,
  s.leaderboard_month_start,
  s.created_at,
  s.id AS score_id
FROM scores s
JOIN games g ON g.id = s.game_id
JOIN game_sessions gs ON gs.id = s.session_id
LEFT JOIN players p ON p.id = s.player_id
WHERE s.leaderboard_eligible = 1
  AND gs.session_type = 'normal';

INSERT OR IGNORE INTO schema_migrations (version, name)
VALUES ('011', 'scores_leaderboards');
