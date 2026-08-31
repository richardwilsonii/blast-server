PRAGMA foreign_keys = ON;

INSERT OR IGNORE INTO games (
  game_code,
  name,
  public_description,
  enabled,
  display_order,
  location_code
)
VALUES
('game_01', 'Placeholder Game 01', 'TBD game description.', 0, 1, 'TBD'),
('game_02', 'Placeholder Game 02', 'TBD game description.', 0, 2, 'TBD'),
('game_03', 'Placeholder Game 03', 'TBD game description.', 0, 3, 'TBD'),
('game_04', 'Placeholder Game 04', 'TBD game description.', 0, 4, 'TBD'),
('game_05', 'Placeholder Game 05', 'TBD game description.', 0, 5, 'TBD'),
('game_06', 'Placeholder Game 06', 'TBD game description.', 0, 6, 'TBD'),
('game_07', 'Placeholder Game 07', 'TBD game description.', 0, 7, 'TBD'),
('game_08', 'Placeholder Game 08', 'TBD game description.', 0, 8, 'TBD'),
('game_09', 'Placeholder Game 09', 'TBD game description.', 0, 9, 'TBD'),
('game_10', 'Placeholder Game 10', 'TBD game description.', 0, 10, 'TBD');

INSERT OR IGNORE INTO game_configs (
  game_id,
  credit_cost,
  min_players,
  max_players,
  time_limit_sec,
  reservation_timeout_sec,
  score_type,
  score_direction,
  score_scope,
  reservation_completion_method,
  reservation_credit_hold_behavior,
  allows_leaderboard,
  allows_replay
)
SELECT
  id,
  1,
  1,
  4,
  300,
  300,
  'points',
  'high_wins',
  'individual',
  'timer',
  'none',
  1,
  1
FROM games
WHERE game_code LIKE 'game_%';

INSERT OR IGNORE INTO game_status (
  game_id,
  availability_state,
  status_message
)
SELECT
  id,
  'offline',
  'Placeholder game not yet configured.'
FROM games
WHERE game_code LIKE 'game_%';

INSERT OR IGNORE INTO schema_migrations (version, name)
VALUES ('009', 'seed_placeholder_games');
