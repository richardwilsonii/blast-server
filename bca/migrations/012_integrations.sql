PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS integration_endpoints (
  id INTEGER PRIMARY KEY,
  provider TEXT NOT NULL
    CHECK(provider IN ('square','otc','booking','cloud','other')),
  endpoint_name TEXT NOT NULL,
  enabled INTEGER NOT NULL DEFAULT 0 CHECK(enabled IN (0,1)),
  config_json TEXT,
  last_sync_at TEXT,
  status TEXT NOT NULL DEFAULT 'disabled'
    CHECK(status IN ('disabled','ready','syncing','error')),
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT,
  UNIQUE(provider, endpoint_name)
);

CREATE TABLE IF NOT EXISTS integration_events (
  id INTEGER PRIMARY KEY,
  provider TEXT NOT NULL
    CHECK(provider IN ('square','otc','booking','cloud','other')),
  external_event_id TEXT,
  event_type TEXT NOT NULL,
  payload_json TEXT,
  processing_status TEXT NOT NULL DEFAULT 'pending'
    CHECK(processing_status IN ('pending','processed','failed','ignored')),
  related_table TEXT,
  related_id INTEGER,
  error_message TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  processed_at TEXT,
  UNIQUE(provider, external_event_id)
);

CREATE INDEX IF NOT EXISTS idx_integration_events_provider_status
ON integration_events(provider, processing_status, created_at);

CREATE INDEX IF NOT EXISTS idx_integration_events_related
ON integration_events(related_table, related_id);

INSERT OR IGNORE INTO integration_endpoints (
  provider,
  endpoint_name,
  enabled,
  status,
  config_json
)
VALUES
('square', 'Square POS Placeholder', 0, 'disabled', json_object('notes', 'Future Square integration placeholder')),
('otc', 'OTC Placeholder', 0, 'disabled', json_object('notes', 'Future Off The Couch integration placeholder')),
('booking', 'Booking Placeholder', 0, 'disabled', json_object('notes', 'Future website/booking integration placeholder')),
('cloud', 'Cloud Reporting Placeholder', 0, 'disabled', json_object('notes', 'Future cloud reporting/sync placeholder'));

INSERT OR IGNORE INTO schema_migrations (version, name)
VALUES ('012', 'integrations');
