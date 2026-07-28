import base64
import hashlib
import importlib
import os
import re
import sqlite3
import sys
from pathlib import Path


PROJECT_MODULES = [
    "app_config",
    "currency_utils",
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


def test_currency_setting_is_validated_and_persisted(tmp_path, monkeypatch):
    api_obj, _, _, _ = fresh_api(tmp_path, monkeypatch)

    assert api_obj.save_settings({"currency": "eur"}) is True
    assert api_obj.get_settings()["currency"] == "EUR"

    assert api_obj.save_settings({"currency": "not-a-currency"}) is True
    assert api_obj.get_settings()["currency"] == "PHP"


def test_light_theme_is_default_and_dark_theme_remains_available():
    project_root = Path(__file__).resolve().parents[1]
    index_source = (project_root / "web" / "index.html").read_text(encoding="utf-8")
    app_source = (project_root / "web" / "app.js").read_text(encoding="utf-8")
    styles_source = (project_root / "web" / "styles.css").read_text(encoding="utf-8")

    assert '<html lang="en">' in index_source
    assert "darkMode: false" in app_source
    assert "savedTheme === 'dark'" in app_source
    assert ".dark {" in styles_source


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


def test_optional_startup_login_locks_api_until_authenticated(tmp_path, monkeypatch):
    api_obj, api_module, _, _ = fresh_api(tmp_path, monkeypatch)

    configured = api_obj.set_profile_password("secure-pass-123", True)
    assert configured["success"] is True
    assert configured["startup_login_enabled"] is True

    # Enabling the preference does not interrupt the current working session,
    # but a fresh application session must start locked.
    assert api_obj.get_startup_auth_state()["authenticated"] is True
    fresh_session = api_module.Api()
    state = fresh_session.get_startup_auth_state()
    assert state["required"] is True
    assert state["authenticated"] is False

    blocked = fresh_session.get_settings()
    assert blocked["auth_required"] is True
    assert fresh_session.authenticate_startup("incorrect")["authenticated"] is False
    assert fresh_session.authenticate_startup("secure-pass-123")["authenticated"] is True
    assert fresh_session.get_settings()["startup_login_enabled"] == "true"

    assert fresh_session.lock_session()["success"] is True
    assert fresh_session.get_settings()["auth_required"] is True
    assert fresh_session.authenticate_startup("secure-pass-123")["authenticated"] is True
    assert fresh_session.set_startup_login_enabled(False)["success"] is True

    unlocked_session = api_module.Api()
    final_state = unlocked_session.get_startup_auth_state()
    assert final_state["required"] is False
    assert final_state["authenticated"] is True


def test_brand_mark_is_wired_into_login_sidebar_and_about_page():
    project_root = Path(__file__).resolve().parents[1]
    brand_path = project_root / "web" / "assets" / "lending-pro-mark.png"
    index_source = (project_root / "web" / "index.html").read_text(encoding="utf-8")
    about_source = (project_root / "web" / "pages" / "about.js").read_text(encoding="utf-8")

    assert brand_path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
    assert index_source.count("assets/lending-pro-mark.png") >= 2
    assert "assets/lending-pro-mark.png" in about_source
    assert 'id="auth-screen"' in index_source


def test_help_content_is_built_only_after_app_initialization():
    project_root = Path(__file__).resolve().parents[1]
    help_source = (project_root / "web" / "pages" / "help.js").read_text(encoding="utf-8")

    assert "get sections()" in help_source
    eager_prefix = help_source.split("get sections()", 1)[0]
    assert "UI.currencyCode()" not in eager_prefix


def test_public_sources_exclude_maintainer_personal_details():
    project_root = Path(__file__).resolve().parents[1]
    text_suffixes = {".bat", ".js", ".json", ".md", ".py", ".sh", ".txt", ".yaml", ".yml"}
    excluded_dirs = {".git", ".venv", "node_modules", "venv", "venv_win"}
    forbidden = (
        "alain.eric" + "@ik.me",
        "/Users/" + "alain",
        "Developed by " + "Alain",
        "Ce" + "bu",
        "Consola" + "cion",
        "Tolo" + "tolo",
    )

    for source_file in project_root.rglob("*"):
        if not source_file.is_file() or source_file.suffix.lower() not in text_suffixes:
            continue
        if excluded_dirs.intersection(source_file.relative_to(project_root).parts):
            continue
        source = source_file.read_text(encoding="utf-8", errors="ignore")
        assert not any(marker.lower() in source.lower() for marker in forbidden), source_file


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


def test_amortization_schedules_reconcile_to_contract_totals():
    from loan_engine import generate_amortization_schedule, get_loan_summary

    cases = [
        (1000, 1, 3),
        (9999.99, 17.5, 7),
        (123456.78, 0, 120),
    ]
    for interest_type in ("fixed", "declining"):
        for principal, rate, term in cases:
            summary = get_loan_summary(principal, rate, interest_type, term)
            schedule = generate_amortization_schedule(
                principal, rate, interest_type, term, "2026-01-31"
            )

            assert len(schedule) == term
            assert round(sum(row["principal_portion"] for row in schedule), 2) == round(principal, 2)
            assert round(sum(row["interest_portion"] for row in schedule), 2) == summary["total_interest"]
            assert round(sum(row["total_due"] for row in schedule), 2) == summary["total_amount"]
            assert schedule[-1]["balance_remaining"] == 0


def test_payment_rejects_overpayment_and_closed_loan(tmp_path, monkeypatch):
    api_obj, _, _, _ = fresh_api(tmp_path, monkeypatch)
    client_id = make_client(api_obj)
    created = api_obj.create_loan(client_id, 1200, 12, "fixed", 3, "2026-01-01")
    loan_id = created["loan_id"]
    total_due = api_obj.get_loan(loan_id)["remaining"]

    rejected = api_obj.record_payment(loan_id, total_due + 0.01, "cash", "2026-02-01")
    assert rejected["success"] is False
    assert api_obj.get_loan(loan_id)["total_paid"] == 0

    payment_id = api_obj.record_payment(loan_id, total_due, "cash", "2026-02-01")
    assert isinstance(payment_id, int)
    assert api_obj.get_loan(loan_id)["status"] == "paid"

    rejected = api_obj.record_payment(loan_id, 1, "cash", "2026-02-02")
    assert rejected["success"] is False


def test_renewal_counts_fully_paid_installments_not_payment_rows(tmp_path, monkeypatch):
    api_obj, _, _, _ = fresh_api(tmp_path, monkeypatch)
    client_id = make_client(api_obj)
    created = api_obj.create_loan(client_id, 6000, 12, "fixed", 6, "2026-01-01")
    loan_id = created["loan_id"]

    for day in range(1, 4):
        assert isinstance(
            api_obj.record_payment(loan_id, 1, "cash", f"2026-02-0{day}"),
            int,
        )
    info = api_obj.get_loan_rollover_info(loan_id)
    assert info["months_paid"] == 0
    assert info["can_renew"] is False

    installment = api_obj.get_loan(loan_id)["schedule"][0]["total_due"]
    assert isinstance(
        api_obj.record_payment(loan_id, installment * 3 - 3, "cash", "2026-02-04"),
        int,
    )
    info = api_obj.get_loan_rollover_info(loan_id)
    assert info["months_paid"] == 3
    assert info["can_renew"] is True


def test_extension_preserves_contract_total_and_payment_allocations(tmp_path, monkeypatch):
    api_obj, _, database, _ = fresh_api(tmp_path, monkeypatch)
    client_id = make_client(api_obj)
    created = api_obj.create_loan(client_id, 1200, 12, "fixed", 3, "2026-01-01")
    loan_id = created["loan_id"]
    payment_id = api_obj.record_payment(loan_id, 100, "cash", "2026-02-01")

    before = api_obj.get_loan(loan_id)
    contract_total = round(before["principal"] + before["total_interest"], 2)
    result = api_obj.extend_loan(loan_id, 2)
    assert result["success"] is True

    after = api_obj.get_loan(loan_id)
    assert after["term_months"] == 5
    assert after["original_term_months"] == 3
    assert len(after["schedule"]) == 5
    assert after["total_interest"] == before["total_interest"]
    assert after["remaining"] == before["remaining"]
    assert round(sum(row["total_due"] for row in after["schedule"]), 2) == contract_total
    assert result["new_monthly_payment"] < before["monthly_payment"]

    conn = database.get_connection()
    allocated = conn.execute(
        "SELECT COALESCE(SUM(amount), 0) FROM payment_allocations WHERE payment_id = ?",
        (payment_id,),
    ).fetchone()[0]
    conn.close()
    assert allocated == 100


def test_overdue_alerts_use_schedule_allocations_after_extension(tmp_path, monkeypatch):
    api_obj, _, _, _ = fresh_api(tmp_path, monkeypatch)
    client_id = make_client(api_obj)
    created = api_obj.create_loan(client_id, 1200, 12, "fixed", 3, "2020-01-01")
    loan_id = created["loan_id"]

    first_installment = api_obj.get_loan(loan_id)["schedule"][0]["total_due"]
    assert isinstance(
        api_obj.record_payment(loan_id, first_installment, "cash", "2020-02-01"),
        int,
    )
    assert api_obj.extend_loan(loan_id, 2)["success"] is True

    loan = api_obj.get_loan(loan_id)
    alerts = api_obj.get_overdue_alerts()
    assert len(alerts) == 1
    assert alerts[0]["missed_count"] == 4
    assert alerts[0]["earliest_due"] == loan["schedule"][1]["due_date"]
    assert alerts[0]["total_overdue_amount"] == loan["remaining"]


def test_dashboard_interest_uses_payment_allocations(tmp_path, monkeypatch):
    api_obj, _, _, _ = fresh_api(tmp_path, monkeypatch)
    client_id = make_client(api_obj)
    created = api_obj.create_loan(client_id, 1200, 12, "fixed", 3, "2026-01-01")
    assert isinstance(
        api_obj.record_payment(created["loan_id"], 100, "cash", "2026-02-01"),
        int,
    )

    stats = api_obj.get_dashboard_stats()
    assert stats["total_collected"] == 100
    assert stats["interest_collected"] == 48


def test_demo_data_uses_production_rates_methods_and_allocations(tmp_path, monkeypatch):
    api_obj, _, database, _ = fresh_api(tmp_path, monkeypatch)
    result = api_obj.toggle_demo_mode(True)
    assert result["success"] is True

    conn = database.get_connection()
    invalid_methods = conn.execute("""
        SELECT COUNT(*) FROM payments
        WHERE payment_method NOT IN ('cash', 'gcash', 'bank_transfer', 'check')
    """).fetchone()[0]
    payment_total = conn.execute(
        "SELECT ROUND(COALESCE(SUM(amount), 0), 2) FROM payments WHERE voided_at IS NULL"
    ).fetchone()[0]
    allocation_total = conn.execute("""
        SELECT ROUND(COALESCE(SUM(pa.amount), 0), 2)
        FROM payment_allocations pa
        JOIN payments p ON p.id = pa.payment_id
        WHERE p.voided_at IS NULL
    """).fetchone()[0]
    sample = conn.execute("""
        SELECT l.interest_rate, l.principal + l.total_interest AS contract_total,
               SUM(a.total_due) AS schedule_total
        FROM loans l
        JOIN amortization_schedule a ON a.loan_id = l.id
        WHERE l.client_id = 'DEMO-LOW-001'
        GROUP BY l.id
    """).fetchone()
    conn.close()

    assert invalid_methods == 0
    assert allocation_total == payment_total
    assert sample["interest_rate"] == 30
    assert round(sample["schedule_total"], 2) == round(sample["contract_total"], 2)
    api_obj.toggle_demo_mode(False)


def test_financial_pdfs_render_with_explicit_rate_semantics(tmp_path, monkeypatch):
    api_obj, _, _, _ = fresh_api(tmp_path, monkeypatch)
    client_id = make_client(api_obj)
    created = api_obj.create_loan(client_id, 15000, 18, "fixed", 6, "2026-01-01")
    pdf_generator = importlib.import_module("pdf_generator")

    for pdf_data in (
        pdf_generator.generate_contract_pdf(created["loan_id"]),
        pdf_generator.generate_amortization_pdf(created["loan_id"]),
    ):
        assert base64.b64decode(pdf_data).startswith(b"%PDF")


def test_demo_distribution_starts_empty_and_demo_is_temporary(tmp_path, monkeypatch):
    monkeypatch.setenv("PH_LENDING_DEMO_ONLY", "1")
    api_obj, _, database, _ = fresh_api(tmp_path, monkeypatch)

    mode = api_obj.get_app_mode()
    assert mode == {
        "name": "Lending Pro Freeware",
        "demo_only": False,
        "demo_edition": True,
        "demo_active": False,
    }
    assert api_obj.get_demo_status() is False
    assert database.get_db_path().endswith("PH-Lending Demo/phlending.db")
    assert api_obj.get_all_clients_simple() == []

    switched = api_obj.toggle_demo_mode(True)
    assert switched == {
        "success": True,
        "demo_active": True,
        "demo_only": True,
        "demo_edition": True,
    }
    assert database.get_db_path().endswith("PH-Lending Demo/phlending_demo.db")
    assert len(api_obj.get_all_clients_simple()) > 0
    assert api_obj.get_profiles() == []
    assert api_obj.restore_backup("anything")["success"] is False
    assert api_obj.create_new_profile("Private")["success"] is False

    restarted, _, restarted_database, _ = fresh_api(tmp_path, monkeypatch)
    assert restarted.get_demo_status() is False
    assert restarted.get_app_mode()["demo_only"] is False
    assert restarted_database.get_db_path().endswith("PH-Lending Demo/phlending.db")
    assert restarted.get_all_clients_simple() == []


def test_penalty_accepts_regular_currency_amount(tmp_path, monkeypatch):
    api_obj, _, _, _ = fresh_api(tmp_path, monkeypatch)
    client_id = make_client(api_obj)
    loan = api_obj.create_loan(client_id, 20000, 10, "fixed", 6, "2026-01-01")

    penalty_id = api_obj.add_penalty(
        loan["loan_id"], client_id, 2500, "missed_payment", "test", "2026-07-26"
    )

    assert isinstance(penalty_id, int)
    penalties = api_obj.get_penalties(client_id=client_id)
    assert penalties[0]["id"] == penalty_id
    assert penalties[0]["amount"] == 2500


def test_extended_loan_model_persists_frequency_fees_kyc_and_security(tmp_path, monkeypatch):
    api_obj, _, _, _ = fresh_api(tmp_path, monkeypatch)
    client_id = api_obj.create_client({
        "first_name": "Extended",
        "last_name": "Borrower",
        "monthly_income": 50000,
        "id_number": "UMID-123",
        "date_of_birth": "1990-01-02",
        "employer": "Example Ltd",
        "occupation": "Manager",
        "gender": "prefer_not_to_say",
    })
    collector = api_obj.add_collector({"name": "Collector One", "contact": "+639000000000"})
    created = api_obj.create_loan(
        client_id, 10000, 18, "fixed", 6, "2026-01-01", None, False,
        "weekly", 200, 100, True, collector["id"],
        [{"name": "Co Maker", "contact": "+639111111111", "relation": "Sibling"}],
        [{"description": "Motorcycle", "collateral_type": "vehicle",
          "estimated_value": 20000, "plate_number": "QA-001"}],
    )

    assert created["success"] is True
    loan = api_obj.get_loan(created["loan_id"])
    client = api_obj.get_client(client_id)
    assert loan["repayment_frequency"] == "weekly"
    assert loan["installment_count"] == 26
    assert loan["disbursed_amount"] == 7900
    assert loan["total_repayment"] == 10000
    assert loan["taeg"] > 0
    assert len(loan["guarantors"]) == 1
    assert len(loan["collateral"]) == 1
    assert client["id_number"] == "UMID-123"
    assert client["employer"] == "Example Ltd"


def test_auto_penalties_are_idempotent_and_portfolio_risk_is_reported(tmp_path, monkeypatch):
    api_obj, _, _, _ = fresh_api(tmp_path, monkeypatch)
    client_id = make_client(api_obj)
    created = api_obj.create_loan(
        client_id, 1200, 12, "fixed", 3, "2020-01-01",
        None, False, "monthly", 0, 0, False,
    )
    assert created["success"] is True
    assert api_obj.save_settings({
        "auto_penalty_enabled": "true",
        "auto_penalty_type": "percentage",
        "auto_penalty_rate": "2",
        "auto_penalty_grace_days": "3",
        "auto_penalty_max_pct": "10",
    }) is True

    first = api_obj.apply_auto_penalties()
    second = api_obj.apply_auto_penalties()
    stats = api_obj.get_dashboard_stats()

    assert first["success"] is True
    assert first["created"] == 3
    assert second["created"] == 0
    assert stats["par_30"] == 100
    assert stats["aging_buckets"]["90_plus"] == 1200


def test_invalid_kyc_update_does_not_lock_database(tmp_path, monkeypatch):
    api_obj, _, _, _ = fresh_api(tmp_path, monkeypatch)
    client_id = make_client(api_obj)

    rejected = api_obj.update_client(client_id, {"date_of_birth": "not-a-date"})
    assert rejected["success"] is False

    created = api_obj.create_loan(client_id, 1200, 12, "fixed", 3, "2026-01-01")
    assert created["success"] is True


def test_money_and_rate_inputs_accept_cent_precision():
    """Prevent browser step validation from rejecting legitimate amounts."""
    pages_dir = Path(__file__).resolve().parents[1] / "web" / "pages"
    decimal_fields = {
        "amount",
        "commission_amount",
        "commission_rate",
        "default_interest_rate",
        "monthly_income",
        "principal",
        "rate",
        "referral_bonus_amount",
    }

    checked = []
    for path in pages_dir.glob("*.js"):
        source = path.read_text(encoding="utf-8")
        for tag in re.findall(r'<input\b[^>]*type="number"[^>]*>', source, re.DOTALL):
            name_match = re.search(r'name="([^"]+)"', tag)
            if not name_match or name_match.group(1) not in decimal_fields:
                continue
            checked.append((path.name, name_match.group(1)))
            assert 'step="0.01"' in tag, f"Cent precision missing in {path.name}: {tag}"

    assert checked


def test_shutdown_stops_local_server_once(tmp_path, monkeypatch):
    api_obj, _, _, _ = fresh_api(tmp_path, monkeypatch)

    class FakeServer:
        shutdown_calls = 0
        close_calls = 0

        def shutdown(self):
            self.shutdown_calls += 1

        def server_close(self):
            self.close_calls += 1

    server = FakeServer()
    api_obj._server = server

    result = api_obj.shutdown_services(force_backup=False)
    assert result["services_stopped"] is True
    assert server.shutdown_calls == 1
    assert server.close_calls == 1
    assert api_obj._server is None

    repeated = api_obj.shutdown_services(force_backup=False)
    assert repeated["already_stopped"] is True
    assert server.shutdown_calls == 1
