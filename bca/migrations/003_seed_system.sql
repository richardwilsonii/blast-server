PRAGMA foreign_keys = ON;

INSERT OR IGNORE INTO roles (role_key, role_name) VALUES
('operator', 'Operator'),
('manager', 'Manager'),
('administrator', 'Administrator');

-- Operator permissions
INSERT OR IGNORE INTO role_permissions (role_id, permission_key)
SELECT id, 'player.lookup' FROM roles WHERE role_key = 'operator';
INSERT OR IGNORE INTO role_permissions (role_id, permission_key)
SELECT id, 'player.create' FROM roles WHERE role_key = 'operator';
INSERT OR IGNORE INTO role_permissions (role_id, permission_key)
SELECT id, 'band.assign' FROM roles WHERE role_key = 'operator';
INSERT OR IGNORE INTO role_permissions (role_id, permission_key)
SELECT id, 'credits.add' FROM roles WHERE role_key = 'operator';
INSERT OR IGNORE INTO role_permissions (role_id, permission_key)
SELECT id, 'games.view' FROM roles WHERE role_key = 'operator';

-- Manager permissions
INSERT OR IGNORE INTO role_permissions (role_id, permission_key)
SELECT id, 'credits.adjust' FROM roles WHERE role_key = 'manager';
INSERT OR IGNORE INTO role_permissions (role_id, permission_key)
SELECT id, 'credits.refund' FROM roles WHERE role_key = 'manager';
INSERT OR IGNORE INTO role_permissions (role_id, permission_key)
SELECT id, 'band.replace' FROM roles WHERE role_key = 'manager';
INSERT OR IGNORE INTO role_permissions (role_id, permission_key)
SELECT id, 'reservation.override' FROM roles WHERE role_key = 'manager';
INSERT OR IGNORE INTO role_permissions (role_id, permission_key)
SELECT id, 'session.override' FROM roles WHERE role_key = 'manager';
INSERT OR IGNORE INTO role_permissions (role_id, permission_key)
SELECT id, 'door.override' FROM roles WHERE role_key = 'manager';
INSERT OR IGNORE INTO role_permissions (role_id, permission_key)
SELECT id, 'game.maintenance' FROM roles WHERE role_key = 'manager';
INSERT OR IGNORE INTO role_permissions (role_id, permission_key)
SELECT id, 'fault.clear' FROM roles WHERE role_key = 'manager';
INSERT OR IGNORE INTO role_permissions (role_id, permission_key)
SELECT id, 'reports.view' FROM roles WHERE role_key = 'manager';

-- Administrator permissions
INSERT OR IGNORE INTO role_permissions (role_id, permission_key)
SELECT id, 'settings.manage' FROM roles WHERE role_key = 'administrator';
INSERT OR IGNORE INTO role_permissions (role_id, permission_key)
SELECT id, 'users.manage' FROM roles WHERE role_key = 'administrator';
INSERT OR IGNORE INTO role_permissions (role_id, permission_key)
SELECT id, 'roles.manage' FROM roles WHERE role_key = 'administrator';
INSERT OR IGNORE INTO role_permissions (role_id, permission_key)
SELECT id, 'audit.view' FROM roles WHERE role_key = 'administrator';
INSERT OR IGNORE INTO role_permissions (role_id, permission_key)
SELECT id, 'backup.manage' FROM roles WHERE role_key = 'administrator';
INSERT OR IGNORE INTO role_permissions (role_id, permission_key)
SELECT id, 'integrations.manage' FROM roles WHERE role_key = 'administrator';

INSERT OR IGNORE INTO system_settings (scope, setting_key, value_json) VALUES
('global', 'venue_timezone', '"America/Los_Angeles"'),
('global', 'default_wallet_mode', '"individual"'),
('global', 'family_wallet_mode_available', 'true'),
('global', 'credits_whole_numbers_only', 'true'),
('global', 'default_reservation_timeout_sec', '300'),
('global', 'default_reservation_credit_hold_behavior', '"none"'),
('global', 'leaderboard_week_start', '"monday"'),
('global', 'test_sessions_public_leaderboard_default', 'false'),
('global', 'backup_local_path', '"/home/blasty/bca/backups"'),
('global', 'backup_cloud_target', '"TBD"');

INSERT OR IGNORE INTO schema_migrations (version, name)
VALUES ('003', 'seed_system');
