import hashlib
import importlib
import os
import sqlite3
import sys


PROJECT_MODULES = [
    "api",
    "backup",
    "database",
    "demo_generator",
    "excel_export",
    "loan_engine",
    "logger",
    "pdf_generator",
]


def app_support_dir(home):
    if sys.platform == "win32":
        return os.path.join(home, "PH-Lending")
    if sys.platform == "darwin":
        return os.path.join(home, "Library", "Application Support", "PH-Lending")
    return os.path.join(home, ".local", "share", "PH-Lending")


def fresh_modules(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("APPDATA", raising=False)
    for name in PROJECT_MODULES:
        sys.modules.pop(name, None)
    api = importlib.import_module("api")
    database = importlib.import_module("database")
    backup = importlib.import_module("backup")
    return api, database, backup


def fresh_api(tmp_path, monkeypatch):
    api, database, backup = fresh_modules(tmp_path, monkeypatch)
    return api.Api(), api, database, backup


def make_client(api_obj, first_name="Ana", last_name="Diaz"):
    return api_obj.create_client({
        "first_name": first_name,
        "last_name": last_name,
        "contact": "09171234567",
        "rating": 3,
    })


def test_payment_allocation_collections_and_void(tmp_path, monkeypatch):
    api_obj, _, _, _ = fresh_api(tmp_path, monkeypatch)
    client_id = make_client(api_obj)
    created = api_obj.create_loan(client_id, 1200, 12, "fixed", 3, "2026-01-01")
    assert created["success"] is True

    loan = api_obj.get_loan(created["loan_id"])
    first_due_date = loan["schedule"][0]["due_date"]
    first_due_amount = loan["schedule"][0]["total_due"]

    payment_id = api_obj.record_payment(
        created["loan_id"], 100, "bank_transfer", "2026-02-01", "partial"
    )
    assert isinstance(payment_id, int)

    rows = api_obj.get_collections_by_date(first_due_date)
    assert len(rows) == 1
    assert rows[0]["scheduled_total_due"] == first_due_amount
    assert rows[0]["total_due"] == round(first_due_amount - 100, 2)

    result = api_obj.void_payment(payment_id, "duplicate entry")
    assert result["success"] is True

    rows = api_obj.get_collections_by_date(first_due_date)
    assert len(rows) == 1
    assert rows[0]["total_due"] == first_due_amount

    loan = api_obj.get_loan(created["loan_id"])
    assert loan["total_paid"] == 0
    assert loan["status"] == "active"


def test_profile_password_uses_pbkdf2_and_upgrades_legacy_hash(tmp_path, monkeypatch):
    api_obj, _, database, _ = fresh_api(tmp_path, monkeypatch)

    result = api_obj.set_profile_password("secret123")
    assert result["success"] is True
    assert api_obj.verify_profile_password("secret123")["valid"] is True
    assert api_obj.verify_profile_password("wrongpass")["valid"] is False

    conn = database.get_connection()
    stored = conn.execute(
        "SELECT value FROM settings WHERE key = 'profile_password'"
    ).fetchone()[0]
    assert stored.startswith("pbkdf2_sha256$")

    legacy = hashlib.sha256("legacy123".encode("utf-8")).hexdigest()
    conn.execute(
        "INSERT OR REPLACE INTO settings (key, value) VALUES ('profile_password', ?)",
        (legacy,),
    )
    conn.commit()
    conn.close()

    assert api_obj.verify_profile_password("legacy123")["valid"] is True

    conn = database.get_connection()
    upgraded = conn.execute(
        "SELECT value FROM settings WHERE key = 'profile_password'"
    ).fetchone()[0]
    conn.close()
    assert upgraded.startswith("pbkdf2_sha256$")


def test_legacy_bank_payment_schema_migrates(tmp_path, monkeypatch):
    support_dir = app_support_dir(str(tmp_path))
    os.makedirs(support_dir, exist_ok=True)
    db_path = os.path.join(support_dir, "phlending.db")

    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE payments (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            loan_id         INTEGER NOT NULL,
            amount          REAL NOT NULL,
            payment_date    TEXT NOT NULL,
            payment_method  TEXT NOT NULL DEFAULT 'cash'
                            CHECK(payment_method IN ('cash', 'gcash', 'bank')),
            notes           TEXT DEFAULT '',
            created_at      TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

    _, database, _ = fresh_modules(tmp_path, monkeypatch)
    database.init_database()

    conn = database.get_connection()
    payments_sql = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'payments'"
    ).fetchone()[0]
    columns = {
        row[1]
        for row in conn.execute("PRAGMA table_info(payments)").fetchall()
    }
    conn.close()

    assert "bank_transfer" in payments_sql
    assert "check" in payments_sql
    assert "voided_at" in columns
    assert "void_reason" in columns


def test_legacy_bank_schema_rebuilds_allocation_foreign_key(tmp_path, monkeypatch):
    support_dir = app_support_dir(str(tmp_path))
    os.makedirs(support_dir, exist_ok=True)
    db_path = os.path.join(support_dir, "phlending.db")

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("""
        CREATE TABLE clients (
            id TEXT PRIMARY KEY,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE loans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id TEXT NOT NULL,
            principal REAL NOT NULL,
            interest_rate REAL NOT NULL,
            interest_type TEXT NOT NULL CHECK(interest_type IN ('fixed', 'declining')),
            term_months INTEGER NOT NULL,
            start_date TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active', 'paid', 'defaulted', 'refinanced')),
            total_interest REAL NOT NULL DEFAULT 0,
            monthly_payment REAL NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
        )
    """)
    conn.execute("""
        CREATE TABLE payments (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            loan_id         INTEGER NOT NULL,
            amount          REAL NOT NULL,
            payment_date    TEXT NOT NULL,
            payment_method  TEXT NOT NULL DEFAULT 'cash'
                            CHECK(payment_method IN ('cash', 'gcash', 'bank')),
            notes           TEXT DEFAULT '',
            created_at      TEXT NOT NULL,
            FOREIGN KEY (loan_id) REFERENCES loans(id) ON DELETE CASCADE
        )
    """)
    conn.execute("""
        CREATE TABLE amortization_schedule (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            loan_id INTEGER NOT NULL,
            month_number INTEGER NOT NULL,
            due_date TEXT NOT NULL,
            principal_portion REAL NOT NULL,
            interest_portion REAL NOT NULL,
            total_due REAL NOT NULL,
            balance_remaining REAL NOT NULL,
            FOREIGN KEY (loan_id) REFERENCES loans(id) ON DELETE CASCADE
        )
    """)
    conn.execute(
        "INSERT INTO clients (id, first_name, last_name, created_at, updated_at) VALUES ('PH-2026-001', 'Ana', 'Diaz', '2026-01-01', '2026-01-01')"
    )
    conn.execute("""
        INSERT INTO loans
            (id, client_id, principal, interest_rate, interest_type, term_months, start_date, status, total_interest, monthly_payment, created_at)
        VALUES (1, 'PH-2026-001', 1000, 10, 'fixed', 1, '2026-01-01', 'active', 100, 1100, '2026-01-01')
    """)
    conn.execute("""
        INSERT INTO amortization_schedule
            (id, loan_id, month_number, due_date, principal_portion, interest_portion, total_due, balance_remaining)
        VALUES (1, 1, 1, '2026-02-01', 1000, 100, 1100, 0)
    """)
    conn.execute("""
        INSERT INTO payments
            (id, loan_id, amount, payment_date, payment_method, notes, created_at)
        VALUES (1, 1, 100, '2026-02-01', 'bank', '', '2026-02-01')
    """)
    conn.commit()
    conn.close()

    _, database, _ = fresh_modules(tmp_path, monkeypatch)
    database.init_database()

    conn = database.get_connection()
    allocation_sql = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'payment_allocations'"
    ).fetchone()[0]
    payment_method = conn.execute(
        "SELECT payment_method FROM payments WHERE id = 1"
    ).fetchone()[0]
    allocation_count = conn.execute(
        "SELECT COUNT(*) FROM payment_allocations WHERE payment_id = 1"
    ).fetchone()[0]
    conn.close()

    assert "payments_legacy" not in allocation_sql
    assert "REFERENCES payments(id)" in allocation_sql
    assert payment_method == "bank_transfer"
    assert allocation_count == 1


def test_backup_restore_replaces_active_profile_safely(tmp_path, monkeypatch):
    api_obj, _, _, _ = fresh_api(tmp_path, monkeypatch)
    first_client = make_client(api_obj, "First", "Client")

    backup_result = api_obj.do_backup_local()
    assert backup_result["success"] is True
    backup_name = "backup_" + backup_result["timestamp"]

    second_client = make_client(api_obj, "Second", "Client")
    assert second_client != first_client

    restore_result = api_obj.restore_backup(backup_name)
    assert restore_result["success"] is True

    clients = api_obj.get_all_clients_simple()
    ids = {client["id"] for client in clients}
    assert first_client in ids
    assert second_client not in ids
