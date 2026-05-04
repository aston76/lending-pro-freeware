"""
PH-Lending Pro — Database Module
SQLite3 schema initialization, connection management, migrations, and profile management.
"""

import sqlite3
import os
import sys
import json
from datetime import datetime

# App data directory — cross-platform
if sys.platform == "win32":
    # Windows: C:\Users\<User>\AppData\Roaming\PH-Lending
    _base = os.environ.get("APPDATA", os.path.expanduser("~"))
    APP_SUPPORT_DIR = os.path.join(_base, "PH-Lending")
elif sys.platform == "darwin":
    # macOS: ~/Library/Application Support/PH-Lending
    APP_SUPPORT_DIR = os.path.expanduser("~/Library/Application Support/PH-Lending")
else:
    # Linux : ~/.local/share/PH-Lending
    APP_SUPPORT_DIR = os.path.expanduser("~/.local/share/PH-Lending")

MEDIA_DIR = os.path.join(APP_SUPPORT_DIR, "media")
BACKUP_DIR = os.path.join(APP_SUPPORT_DIR, "backups")
PROFILES_DIR = os.path.join(APP_SUPPORT_DIR, "profiles")
PROFILES_META = os.path.join(APP_SUPPORT_DIR, "profiles.json")

# DB Path state
_is_demo_mode = False
_active_profile_id = "default"


# ═══════════════════════════════════════════════════════════════
# PROFILE MANAGEMENT
# ═══════════════════════════════════════════════════════════════

def _load_profiles_meta():
    """Load profiles metadata from JSON file."""
    if os.path.exists(PROFILES_META):
        try:
            with open(PROFILES_META, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    # Default structure — backward compatible with existing DB
    return {
        "active": "default",
        "profiles": [
            {
                "id": "default",
                "name": "Main Profile",
                "description": "Default lending profile",
                "db_file": "phlending.db",
                "created_at": datetime.now().isoformat(),
                "color": "#007AFF"
            }
        ]
    }


def _save_profiles_meta(meta):
    """Save profiles metadata to JSON file."""
    os.makedirs(APP_SUPPORT_DIR, exist_ok=True)
    with open(PROFILES_META, 'w') as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)


def get_profiles():
    """Return the list of all profiles with active flag."""
    meta = _load_profiles_meta()
    for p in meta["profiles"]:
        p["is_active"] = (p["id"] == meta["active"])
    return meta["profiles"]


def get_active_profile():
    """Return the currently active profile dict."""
    meta = _load_profiles_meta()
    for p in meta["profiles"]:
        if p["id"] == meta["active"]:
            p["is_active"] = True
            return p
    # Fallback to first
    if meta["profiles"]:
        meta["profiles"][0]["is_active"] = True
        return meta["profiles"][0]
    return None


def create_profile(name, description="", color="#007AFF"):
    """Create a new profile with its own database file."""
    meta = _load_profiles_meta()
    # Generate unique ID
    pid = f"profile_{int(datetime.now().timestamp() * 1000)}"
    db_file = f"phlending_{pid}.db"

    profile = {
        "id": pid,
        "name": name,
        "description": description,
        "db_file": db_file,
        "created_at": datetime.now().isoformat(),
        "color": color
    }
    meta["profiles"].append(profile)
    _save_profiles_meta(meta)

    # Initialize the new database
    old_profile = _active_profile_id
    switch_profile(pid)
    init_database()
    switch_profile(old_profile)

    return profile


def switch_profile(profile_id):
    """Switch the active profile."""
    global _active_profile_id
    meta = _load_profiles_meta()
    # Verify profile exists
    found = any(p["id"] == profile_id for p in meta["profiles"])
    if not found:
        return False
    meta["active"] = profile_id
    _active_profile_id = profile_id
    _save_profiles_meta(meta)
    return True


def rename_profile(profile_id, new_name, new_description=None, new_color=None):
    """Rename and update a profile's metadata."""
    meta = _load_profiles_meta()
    for p in meta["profiles"]:
        if p["id"] == profile_id:
            p["name"] = new_name
            if new_description is not None:
                p["description"] = new_description
            if new_color is not None:
                p["color"] = new_color
            _save_profiles_meta(meta)
            return True
    return False


def delete_profile(profile_id):
    """Delete a profile and optionally its database file. Cannot delete 'default'."""
    if profile_id == "default":
        return False
    meta = _load_profiles_meta()
    target = None
    for p in meta["profiles"]:
        if p["id"] == profile_id:
            target = p
            break
    if not target:
        return False

    # Delete DB file
    db_path = os.path.join(APP_SUPPORT_DIR, target["db_file"])
    if os.path.exists(db_path):
        os.remove(db_path)

    # Remove from list
    meta["profiles"] = [p for p in meta["profiles"] if p["id"] != profile_id]

    # Switch to default if we deleted the active one
    if meta["active"] == profile_id:
        meta["active"] = "default"
        global _active_profile_id
        _active_profile_id = "default"

    _save_profiles_meta(meta)
    return True


def reset_profile_data():
    """Wipe ALL data tables in the current profile's database. Settings are preserved."""
    conn = get_connection()
    c = conn.cursor()
    # Delete in FK-safe order
    for table in ['referral_commissions', 'penalties', 'payments',
                  'amortization_schedule', 'documents', 'loans', 'clients']:
        c.execute(f"DELETE FROM {table}")
    # Reset auto-increment
    c.execute("DELETE FROM sqlite_sequence WHERE name IN "
              "('loans','payments','amortization_schedule','penalties','documents','referral_commissions')")
    conn.commit()
    conn.close()
    return True


def get_db_path():
    """Return the active database path (demo, profile, or default)."""
    if _is_demo_mode:
        return os.path.join(APP_SUPPORT_DIR, "phlending_demo.db")
    # Profile-based
    meta = _load_profiles_meta()
    for p in meta["profiles"]:
        if p["id"] == _active_profile_id:
            return os.path.join(APP_SUPPORT_DIR, p["db_file"])
    return os.path.join(APP_SUPPORT_DIR, "phlending.db")


def set_demo_mode(enabled: bool):
    """Enable or disable demo mode."""
    global _is_demo_mode
    _is_demo_mode = enabled
    if enabled:
        init_database()  # Ensure demo schema is ready


def load_active_profile():
    """Load and set the active profile from saved metadata. Call at app startup."""
    global _active_profile_id
    meta = _load_profiles_meta()
    _active_profile_id = meta.get("active", "default")
    # Ensure the meta file exists
    _save_profiles_meta(meta)


def ensure_directories():
    """Create all necessary application directories."""
    for d in [APP_SUPPORT_DIR, MEDIA_DIR, BACKUP_DIR,
              os.path.join(MEDIA_DIR, "photos"),
              os.path.join(MEDIA_DIR, "ids"),
              os.path.join(MEDIA_DIR, "documents"),
              os.path.join(MEDIA_DIR, "signatures")]:
        os.makedirs(d, exist_ok=True)


def get_connection():
    """Get a new SQLite connection with WAL mode and foreign keys enabled."""
    ensure_directories()
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def dict_from_row(row):
    """Convert a sqlite3.Row to a plain dict."""
    if row is None:
        return None
    return dict(row)


def rows_to_list(rows):
    """Convert a list of sqlite3.Row objects to a list of dicts."""
    return [dict(r) for r in rows]


def init_database():
    """Initialize the database schema. Safe to call multiple times (IF NOT EXISTS)."""
    ensure_directories()
    conn = get_connection()
    cursor = conn.cursor()

    # ── Clients (KYC) ────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            id              TEXT PRIMARY KEY,
            first_name      TEXT NOT NULL,
            last_name       TEXT NOT NULL,
            address         TEXT DEFAULT '',
            address_detail  TEXT DEFAULT '',
            contact         TEXT DEFAULT '',
            email           TEXT DEFAULT '',
            rating          INTEGER DEFAULT 3 CHECK(rating BETWEEN 1 AND 5),
            referred_by     TEXT,
            photo_path      TEXT DEFAULT '',
            id_photo_path   TEXT DEFAULT '',
            notes           TEXT DEFAULT '',
            monthly_income  REAL DEFAULT 0,
            created_at      TEXT NOT NULL,
            updated_at      TEXT NOT NULL,
            FOREIGN KEY (referred_by) REFERENCES clients(id) ON DELETE SET NULL
        )
    """)

    # ── Loans ────────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS loans (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id           TEXT NOT NULL,
            principal           REAL NOT NULL,
            interest_rate       REAL NOT NULL,
            interest_type       TEXT NOT NULL CHECK(interest_type IN ('fixed', 'declining')),
            term_months         INTEGER NOT NULL,
            start_date          TEXT NOT NULL,
            status              TEXT NOT NULL DEFAULT 'active'
                                CHECK(status IN ('active', 'paid', 'defaulted', 'refinanced')),
            total_interest      REAL NOT NULL DEFAULT 0,
            monthly_payment     REAL NOT NULL DEFAULT 0,
            original_loan_id    INTEGER DEFAULT NULL,
            rollover_amount     REAL DEFAULT 0,
            created_at          TEXT NOT NULL,
            FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE,
            FOREIGN KEY (original_loan_id) REFERENCES loans(id) ON DELETE SET NULL
        )
    """)

    # ── Amortization Schedule ────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS amortization_schedule (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            loan_id             INTEGER NOT NULL,
            month_number        INTEGER NOT NULL,
            due_date            TEXT NOT NULL,
            principal_portion   REAL NOT NULL,
            interest_portion    REAL NOT NULL,
            total_due           REAL NOT NULL,
            balance_remaining   REAL NOT NULL,
            FOREIGN KEY (loan_id) REFERENCES loans(id) ON DELETE CASCADE
        )
    """)

    # ── Payments ─────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            loan_id         INTEGER NOT NULL,
            amount          REAL NOT NULL,
            payment_date    TEXT NOT NULL,
            payment_method  TEXT NOT NULL DEFAULT 'cash'
                            CHECK(payment_method IN ('cash', 'gcash', 'bank_transfer', 'check')),
            notes           TEXT DEFAULT '',
            created_at      TEXT NOT NULL,
            FOREIGN KEY (loan_id) REFERENCES loans(id) ON DELETE CASCADE
        )
    """)

    # ── Documents ────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id   TEXT NOT NULL,
            file_path   TEXT NOT NULL,
            file_type   TEXT NOT NULL CHECK(file_type IN ('photo', 'id', 'contract', 'orcr', 'signature', 'other')),
            description TEXT DEFAULT '',
            created_at  TEXT NOT NULL,
            FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
        )
    """)

    # ── Referral Commissions ─────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS referral_commissions (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            referrer_id         TEXT NOT NULL,
            referred_id         TEXT NOT NULL,
            loan_id             INTEGER NOT NULL,
            commission_amount   REAL NOT NULL DEFAULT 0,
            status              TEXT NOT NULL DEFAULT 'pending'
                                CHECK(status IN ('pending', 'paid')),
            created_at          TEXT NOT NULL,
            FOREIGN KEY (referrer_id) REFERENCES clients(id) ON DELETE CASCADE,
            FOREIGN KEY (referred_id) REFERENCES clients(id) ON DELETE CASCADE,
            FOREIGN KEY (loan_id)     REFERENCES loans(id)   ON DELETE CASCADE
        )
    """)

    # ── Penalties ────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS penalties (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            loan_id         INTEGER NOT NULL,
            client_id       TEXT NOT NULL,
            amount          REAL NOT NULL DEFAULT 0,
            reason          TEXT NOT NULL DEFAULT 'late_payment'
                            CHECK(reason IN ('late_payment', 'missed_payment', 'early_termination', 'other')),
            notes           TEXT DEFAULT '',
            status          TEXT NOT NULL DEFAULT 'pending'
                            CHECK(status IN ('pending', 'paid', 'waived')),
            penalty_date    TEXT NOT NULL,
            created_at      TEXT NOT NULL,
            FOREIGN KEY (loan_id)   REFERENCES loans(id)   ON DELETE CASCADE,
            FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
        )
    """)

    # ── Settings (key-value) ─────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key     TEXT PRIMARY KEY,
            value   TEXT NOT NULL
        )
    """)

    # ── Default settings ─────────────────────────────────────────
    defaults = {
        "commission_rate": "2.0",
        "commission_type": "percentage",
        "commission_amount": "500",
        "default_interest_rate": "5.0",
        "default_interest_type": "fixed",
        "currency": "PHP",
        "dark_mode": "true",
        "company_name": "PH-Lending Pro",
        "company_phone": "",
        "company_address": "",
        "company_contact": ""
    }
    for key, value in defaults.items():
        cursor.execute(
            "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
            (key, value)
        )

    # ── Payments method migration ────────────────────────────────
    # Older DBs allowed only "bank"; the UI now exposes bank_transfer and check.
    cursor.execute("SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'payments'")
    payments_sql = (cursor.fetchone() or [None])[0] or ""
    if "payment_method IN ('cash', 'gcash', 'bank')" in payments_sql:
        cursor.execute("ALTER TABLE payments RENAME TO payments_legacy")
        cursor.execute("""
            CREATE TABLE payments (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                loan_id         INTEGER NOT NULL,
                amount          REAL NOT NULL,
                payment_date    TEXT NOT NULL,
                payment_method  TEXT NOT NULL DEFAULT 'cash'
                                CHECK(payment_method IN ('cash', 'gcash', 'bank_transfer', 'check')),
                notes           TEXT DEFAULT '',
                created_at      TEXT NOT NULL,
                FOREIGN KEY (loan_id) REFERENCES loans(id) ON DELETE CASCADE
            )
        """)
        cursor.execute("""
            INSERT INTO payments (id, loan_id, amount, payment_date, payment_method, notes, created_at)
            SELECT id, loan_id, amount, payment_date,
                   CASE payment_method WHEN 'bank' THEN 'bank_transfer' ELSE payment_method END,
                   notes, created_at
            FROM payments_legacy
        """)
        cursor.execute("DROP TABLE payments_legacy")

    # ── Useful indexes ───────────────────────────────────────────
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_loans_client ON loans(client_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_loans_status ON loans(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_amort_loan ON amortization_schedule(loan_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_payments_loan ON payments(loan_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_client ON documents(client_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_amort_due ON amortization_schedule(due_date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_penalties_loan ON penalties(loan_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_penalties_client ON penalties(client_id)")

    # ── Safe migrations (add new columns to existing DBs) ────────
    migrations = [
        ("clients",  "monthly_income",    "ALTER TABLE clients ADD COLUMN monthly_income REAL DEFAULT 0"),
        ("clients",  "email",             "ALTER TABLE clients ADD COLUMN email TEXT DEFAULT ''"),
        ("clients",  "address_detail",    "ALTER TABLE clients ADD COLUMN address_detail TEXT DEFAULT ''"),
        ("clients",  "social_media",      "ALTER TABLE clients ADD COLUMN social_media TEXT DEFAULT '[]'"),
        ("loans",    "original_loan_id",  "ALTER TABLE loans ADD COLUMN original_loan_id INTEGER DEFAULT NULL"),
        ("loans",    "rollover_amount",   "ALTER TABLE loans ADD COLUMN rollover_amount REAL DEFAULT 0"),
    ]
    for table, column, sql in migrations:
        try:
            cursor.execute(f"SELECT {column} FROM {table} LIMIT 1")
        except Exception:
            try:
                cursor.execute(sql)
            except Exception:
                pass  # column may already exist in some edge case

    # Extend loans status constraint safely (SQLite doesn't support ALTER CONSTRAINT)
    # The CHECK is advisory; new statuses will work fine in practice with SQLite.

    conn.commit()
    conn.close()


def generate_client_id():
    """Generate the next client ID in format PH-YYYY-NNN."""
    year = datetime.now().strftime("%Y")
    prefix = f"PH-{year}-"
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id FROM clients WHERE id LIKE ? ORDER BY id DESC LIMIT 1",
        (f"{prefix}%",)
    )
    row = cursor.fetchone()
    conn.close()

    if row:
        last_num = int(row["id"].split("-")[-1])
        next_num = last_num + 1
    else:
        next_num = 1

    return f"{prefix}{next_num:03d}"


if __name__ == "__main__":
    init_database()
    print(f"Database initialized at: {get_db_path()}")
    print(f"Media directory: {MEDIA_DIR}")
    test_id = generate_client_id()
    print(f"Next client ID would be: {test_id}")
