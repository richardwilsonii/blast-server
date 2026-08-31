PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS wallets (
  id INTEGER PRIMARY KEY,
  owner_type TEXT NOT NULL CHECK(owner_type IN ('account','player')),
  owner_account_id INTEGER REFERENCES accounts(id),
  owner_player_id INTEGER REFERENCES players(id),
  status TEXT NOT NULL DEFAULT 'active'
    CHECK(status IN ('active','frozen','closed')),
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT,
  CHECK(
    (owner_type = 'account' AND owner_account_id IS NOT NULL AND owner_player_id IS NULL)
    OR
    (owner_type = 'player' AND owner_player_id IS NOT NULL AND owner_account_id IS NULL)
  )
);

CREATE TABLE IF NOT EXISTS credit_transactions (
  id INTEGER PRIMARY KEY,
  wallet_id INTEGER NOT NULL REFERENCES wallets(id),
  tx_type TEXT NOT NULL CHECK(tx_type IN (
    'purchase',
    'spend',
    'refund',
    'adjustment',
    'promotion',
    'void',
    'correction',
    'transfer_in',
    'transfer_out'
  )),
  amount_credits INTEGER NOT NULL CHECK(amount_credits <> 0),
  balance_after INTEGER,
  source_type TEXT,
  source_id INTEGER,
  actor_user_id INTEGER REFERENCES admin_users(id),
  related_transaction_id INTEGER REFERENCES credit_transactions(id),
  idempotency_key TEXT UNIQUE,
  reason TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS credit_holds (
  id INTEGER PRIMARY KEY,
  wallet_id INTEGER NOT NULL REFERENCES wallets(id),
  reservation_id INTEGER,
  amount_credits INTEGER NOT NULL CHECK(amount_credits > 0),
  status TEXT NOT NULL DEFAULT 'active'
    CHECK(status IN ('active','released','expired','converted')),
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  released_at TEXT
);

CREATE TABLE IF NOT EXISTS credit_packages (
  id INTEGER PRIMARY KEY,
  package_code TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  price_cents INTEGER,
  base_credits INTEGER NOT NULL DEFAULT 0 CHECK(base_credits >= 0),
  bonus_credits INTEGER NOT NULL DEFAULT 0 CHECK(bonus_credits >= 0),
  active INTEGER NOT NULL DEFAULT 0 CHECK(active IN (0,1)),
  starts_at TEXT,
  ends_at TEXT,
  pos_sku TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS payments (
  id INTEGER PRIMARY KEY,
  provider TEXT NOT NULL CHECK(provider IN ('manual','square','otc')),
  external_payment_id TEXT,
  amount_cents INTEGER,
  status TEXT NOT NULL DEFAULT 'completed'
    CHECK(status IN ('pending','completed','failed','refunded','voided')),
  account_id INTEGER REFERENCES accounts(id),
  player_id INTEGER REFERENCES players(id),
  wallet_id INTEGER REFERENCES wallets(id),
  credits_awarded INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_wallets_owner_account
ON wallets(owner_account_id);

CREATE INDEX IF NOT EXISTS idx_wallets_owner_player
ON wallets(owner_player_id);

CREATE INDEX IF NOT EXISTS idx_credit_transactions_wallet_created
ON credit_transactions(wallet_id, created_at);

CREATE INDEX IF NOT EXISTS idx_credit_holds_wallet_status
ON credit_holds(wallet_id, status);

CREATE VIEW IF NOT EXISTS v_wallet_balances AS
SELECT
  w.id AS wallet_id,
  COALESCE(SUM(ct.amount_credits), 0) AS balance
FROM wallets w
LEFT JOIN credit_transactions ct ON ct.wallet_id = w.id
GROUP BY w.id;

CREATE VIEW IF NOT EXISTS v_wallet_available_balances AS
SELECT
  w.id AS wallet_id,
  COALESCE(t.balance, 0) - COALESCE(h.active_holds, 0) AS available_credits
FROM wallets w
LEFT JOIN (
  SELECT wallet_id, SUM(amount_credits) AS balance
  FROM credit_transactions
  GROUP BY wallet_id
) t ON t.wallet_id = w.id
LEFT JOIN (
  SELECT wallet_id, SUM(amount_credits) AS active_holds
  FROM credit_holds
  WHERE status = 'active'
  GROUP BY wallet_id
) h ON h.wallet_id = w.id;

INSERT OR IGNORE INTO credit_packages (package_code, name, active) VALUES
('TBD_SMALL', 'TBD Small Credit Package', 0),
('TBD_MEDIUM', 'TBD Medium Credit Package', 0),
('TBD_LARGE', 'TBD Large Credit Package', 0);

INSERT OR IGNORE INTO schema_migrations (version, name)
VALUES ('007', 'wallets_credits');
