#!/usr/bin/env python3
import sqlite3
import hashlib
import secrets
import getpass
from pathlib import Path

DB_PATH = Path.home() / "bca" / "db" / "bca.sqlite"

def hash_secret(secret: str) -> str:
    salt = secrets.token_hex(16)
    iterations = 260000
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        secret.encode("utf-8"),
        salt.encode("utf-8"),
        iterations
    ).hex()
    return f"pbkdf2_sha256${iterations}${salt}${digest}"

username = input("Admin username: ").strip()
display_name = input("Display name: ").strip()

password = getpass.getpass("Admin password: ")
password2 = getpass.getpass("Confirm password: ")

if password != password2:
    raise SystemExit("Passwords do not match.")

pin = getpass.getpass("Override PIN: ")
pin2 = getpass.getpass("Confirm override PIN: ")

if pin != pin2:
    raise SystemExit("PINs do not match.")

if len(pin) < 4:
    raise SystemExit("Override PIN should be at least 4 digits.")

password_hash = hash_secret(password)
pin_hash = hash_secret(pin)

con = sqlite3.connect(DB_PATH)
con.execute("PRAGMA foreign_keys = ON;")

try:
    with con:
        con.execute("""
            INSERT INTO admin_users (
                username,
                display_name,
                password_hash,
                override_pin_hash,
                active,
                must_change_password
            )
            VALUES (?, ?, ?, ?, 1, 0)
        """, (username, display_name, password_hash, pin_hash))

        user_id = con.execute(
            "SELECT id FROM admin_users WHERE username = ?",
            (username,)
        ).fetchone()[0]

        admin_role_id = con.execute(
            "SELECT id FROM roles WHERE role_key = 'administrator'"
        ).fetchone()[0]

        manager_role_id = con.execute(
            "SELECT id FROM roles WHERE role_key = 'manager'"
        ).fetchone()[0]

        operator_role_id = con.execute(
            "SELECT id FROM roles WHERE role_key = 'operator'"
        ).fetchone()[0]

        con.execute(
            "INSERT OR IGNORE INTO user_roles (user_id, role_id) VALUES (?, ?)",
            (user_id, admin_role_id)
        )
        con.execute(
            "INSERT OR IGNORE INTO user_roles (user_id, role_id) VALUES (?, ?)",
            (user_id, manager_role_id)
        )
        con.execute(
            "INSERT OR IGNORE INTO user_roles (user_id, role_id) VALUES (?, ?)",
            (user_id, operator_role_id)
        )

        con.execute("""
            INSERT INTO audit_log (
                event_type,
                actor_user_id,
                target_type,
                target_id,
                after_json,
                reason
            )
            VALUES (
                'admin_user.created',
                ?,
                'admin_users',
                ?,
                json_object('username', ?, 'display_name', ?),
                'Initial admin setup'
            )
        """, (user_id, user_id, username, display_name))

    print(f"Created admin user: {username}")

except sqlite3.IntegrityError as e:
    raise SystemExit(f"Could not create admin user: {e}")

finally:
    con.close()
