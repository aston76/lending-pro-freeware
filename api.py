"""
Lending Pro Freeware — Main API
Exposed to the frontend via pywebview's js_api bridge.
All methods are callable from JavaScript as pywebview.api.<method_name>()
"""

import os
import sys
import hmac
import secrets
import hashlib
import math
import json
import sqlite3
import base64
import binascii
import subprocess
import webbrowser
import traceback
import threading
import time
from datetime import datetime

from dateutil.relativedelta import relativedelta

import logger as app_logger  # persistent error logger
from app_config import APP_NAME, DEMO_ONLY
from currency_utils import normalize_currency

from database import (
    get_connection, dict_from_row, rows_to_list,
    init_database, generate_client_id, MEDIA_DIR, APP_SUPPORT_DIR,
    set_demo_mode, load_active_profile,
    get_profiles as db_get_profiles, get_active_profile as db_get_active_profile,
    create_profile as db_create_profile, switch_profile as db_switch_profile,
    rename_profile as db_rename_profile, delete_profile as db_delete_profile,
    reset_profile_data, get_db_path
)
from loan_engine import (
    advance_due_date, distribute_money, generate_amortization_schedule,
    get_installment_count, get_loan_summary,
)
from pdf_generator import generate_contract_pdf, generate_receipt_pdf, generate_amortization_pdf
from excel_export import export_all_to_excel, export_selective
from backup import (
    backup_local, get_backup_status, list_backups,
    sync_to_drive, open_drive_folder, is_drive_configured, check_internet,
    restore_local_backup
)

PDF_DIR = os.path.join(APP_SUPPORT_DIR, "pdfs")
os.makedirs(PDF_DIR, exist_ok=True)

VALID_PAYMENT_METHODS = {"cash", "gcash", "bank_transfer", "check"}
PAYMENT_METHOD_ALIASES = {
    "bank": "bank_transfer",
    "bank transfer": "bank_transfer",
    "bank-transfer": "bank_transfer",
}
PASSWORD_HASH_ALGO = "pbkdf2_sha256"
PASSWORD_HASH_ITERATIONS = 260_000


def _normalize_payment_method(method):
    normalized = str(method or "cash").strip().lower()
    normalized = PAYMENT_METHOD_ALIASES.get(normalized, normalized)
    if normalized not in VALID_PAYMENT_METHODS:
        raise ValueError(
            "Invalid payment method. Use cash, gcash, bank_transfer, or check."
        )
    return normalized


def _loan_repayment_total(loan):
    """Return the stored repayment total, with a legacy-loan fallback."""
    try:
        stored = float(loan["total_repayment"] or 0)
    except (KeyError, TypeError, ValueError, IndexError):
        stored = 0.0
    if stored > 0:
        return round(stored, 2)
    return round(float(loan["principal"] or 0) + float(loan["total_interest"] or 0), 2)


def _hash_profile_password(password, salt=None, iterations=PASSWORD_HASH_ITERATIONS):
    """Hash a profile password with PBKDF2 and return a portable encoded value."""
    raw_password = str(password or "")
    if not raw_password:
        raise ValueError("Password is required.")
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        raw_password.encode("utf-8"),
        salt,
        int(iterations),
    )
    return f"{PASSWORD_HASH_ALGO}${int(iterations)}${salt.hex()}${digest.hex()}"


def _verify_profile_password(raw_password, stored_hash):
    """Verify PBKDF2 hashes and legacy SHA-256 hashes."""
    stored_hash = str(stored_hash or "")
    raw_password = str(raw_password or "")
    if not raw_password or not stored_hash:
        return False, False

    parts = stored_hash.split("$")
    if len(parts) == 4 and parts[0] == PASSWORD_HASH_ALGO:
        try:
            iterations = int(parts[1])
            salt = bytes.fromhex(parts[2])
            expected = bytes.fromhex(parts[3])
        except (TypeError, ValueError):
            return False, False
        actual = hashlib.pbkdf2_hmac(
            "sha256",
            raw_password.encode("utf-8"),
            salt,
            iterations,
        )
        return hmac.compare_digest(actual, expected), False

    # Backward compatibility for existing SHA-256-only profile passwords.
    if len(stored_hash) == 64:
        legacy = hashlib.sha256(raw_password.encode("utf-8")).hexdigest()
        return hmac.compare_digest(legacy, stored_hash), True

    return False, False


def _open_native(targets, app=None):
    """Open file paths or URLs with the OS default application."""
    if isinstance(targets, (list, tuple)):
        items = [str(t) for t in targets if t]
    else:
        items = [str(targets)] if targets else []
    if not items:
        return False

    if sys.platform == "win32":
        for item in items:
            os.startfile(item)  # type: ignore[attr-defined]
        return True

    if sys.platform == "darwin":
        cmd = ["open"]
        if app:
            cmd.extend(["-a", app])
        cmd.extend(items)
        subprocess.Popen(cmd)
        return True

    opener = "xdg-open"
    for item in items:
        subprocess.Popen([opener, item])
    return True


def _camera_worker(title, queue):
    import cv2
    import base64
    try:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            queue.put({"success": False, "error": "No camera detected from OS level."})
            return
            
        cv2.namedWindow(title, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(title, 800, 600)
        
        captured_frame = None
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            display_frame = frame.copy()
            cv2.putText(display_frame, "SPACE=Capture, ESC=Cancel", (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            cv2.imshow(title, display_frame)
            
            key = cv2.waitKey(1)
            # ESC key to cancel
            if key == 27:
                break
            # SPACE key to capture
            elif key == 32:
                captured_frame = frame
                break
                
        cap.release()
        cv2.destroyWindow(title)
        cv2.waitKey(1) # MacOS fix to fully close the window
        
        if captured_frame is not None:
            _, buffer = cv2.imencode('.png', captured_frame)
            b64_str = base64.b64encode(buffer).decode('utf-8')
            queue.put({"success": True, "b64": b64_str})
        else:
            queue.put({"success": False, "error": "Capture cancelled by user."})

    except Exception as e:
        queue.put({"success": False, "error": f"OpenCV Error: {e}"})


class Api:
    """API class exposed to the pywebview JavaScript frontend."""

    _AUTH_EXEMPT_METHODS = frozenset({
        "authenticate_startup",
        "get_app_mode",
        "get_startup_auth_state",
        "quit_app",
        "shutdown_services",
    })

    def __getattribute__(self, name):
        """Block public API calls while the optional startup lock is active."""
        attribute = object.__getattribute__(self, name)
        if name.startswith("_") or name in object.__getattribute__(self, "_AUTH_EXEMPT_METHODS"):
            return attribute
        if not callable(attribute):
            return attribute
        try:
            locked = (
                object.__getattribute__(self, "_startup_login_required")
                and not object.__getattribute__(self, "_session_authenticated")
            )
        except AttributeError:
            locked = False
        if not locked:
            return attribute

        def authentication_required(*_args, **_kwargs):
            return {
                "success": False,
                "auth_required": True,
                "error": "Unlock this profile to continue.",
            }

        return authentication_required

    def __init__(self):
        self._demo_only = DEMO_ONLY
        self._is_demo = False
        self._startup_login_required = False
        self._session_authenticated = True
        self._login_failures = 0
        self._login_blocked_until = 0.0
        self._window = None
        self._server = None
        self._shutdown_started = False
        self._shutdown_lock = threading.Lock()
        load_active_profile()
        set_demo_mode(False)
        init_database()
        self._reset_startup_auth_session()

    def _read_startup_security(self):
        """Read startup lock settings without exposing the stored password hash."""
        conn = get_connection()
        try:
            rows = conn.execute(
                """
                SELECT key, value FROM settings
                WHERE key IN ('password_enabled', 'profile_password', 'startup_login_enabled', 'company_name')
                """
            ).fetchall()
        finally:
            conn.close()
        settings = {row["key"]: row["value"] for row in rows}
        password_ready = (
            settings.get("password_enabled") == "true"
            and bool(settings.get("profile_password"))
        )
        login_enabled = password_ready and settings.get("startup_login_enabled") == "true"
        return {
            "password_ready": password_ready,
            "login_enabled": login_enabled,
            "password_hash": settings.get("profile_password", ""),
            "company_name": settings.get("company_name") or APP_NAME,
        }

    def _reset_startup_auth_session(self):
        """Apply the active profile's startup policy to a fresh session."""
        security = self._read_startup_security()
        self._startup_login_required = bool(security["login_enabled"])
        self._session_authenticated = not self._startup_login_required
        self._login_failures = 0
        self._login_blocked_until = 0.0

    def _is_restricted_demo(self):
        return self._demo_only and self._is_demo

    def _ensure_demo_data(self):
        """Populate the isolated demo database when it is empty."""
        conn = get_connection()
        try:
            count = conn.execute("SELECT COUNT(*) FROM clients").fetchone()[0]
        finally:
            conn.close()
        if count == 0:
            import demo_generator
            demo_generator.generate_demo_data()

    def _audit_event(self, cursor, event_type, entity_type, entity_id="", details=None):
        """Write a compact business audit event inside the caller transaction."""
        try:
            cursor.execute("""
                INSERT INTO audit_events (event_type, entity_type, entity_id, details, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                event_type,
                entity_type,
                str(entity_id or ""),
                json.dumps(details or {}, ensure_ascii=False),
                datetime.now().isoformat()
            ))
        except Exception as e:
            app_logger.warning("Audit event skipped: %s", e)

    def _allocate_payment(self, cursor, loan_id, payment_id, amount):
        """
        Allocate a payment to the earliest unpaid installments.
        This keeps the collection calendar deterministic even with partial payments.
        """
        remaining_amount = round(float(amount), 2)
        if remaining_amount <= 0:
            return

        cursor.execute("""
            SELECT
                a.id,
                a.total_due,
                COALESCE((
                    SELECT SUM(pa.amount)
                    FROM payment_allocations pa
                    JOIN payments p ON p.id = pa.payment_id
                    WHERE pa.schedule_id = a.id
                      AND p.voided_at IS NULL
                ), 0) AS already_allocated
            FROM amortization_schedule a
            WHERE a.loan_id = ?
            ORDER BY a.month_number ASC
        """, (loan_id,))

        now = datetime.now().isoformat()
        for schedule in cursor.fetchall():
            if remaining_amount <= 0:
                break
            open_amount = round(schedule["total_due"] - schedule["already_allocated"], 2)
            if open_amount <= 0:
                continue
            allocated = min(remaining_amount, open_amount)
            cursor.execute("""
                INSERT OR REPLACE INTO payment_allocations
                    (payment_id, schedule_id, amount, created_at)
                VALUES (?, ?, ?, ?)
            """, (payment_id, schedule["id"], round(allocated, 2), now))
            remaining_amount = round(remaining_amount - allocated, 2)

    def _recompute_loan_status(self, cursor, loan_id):
        """Mark a loan paid or active based on non-voided payments."""
        cursor.execute("SELECT principal, total_interest, total_repayment, status FROM loans WHERE id = ?", (loan_id,))
        loan = cursor.fetchone()
        if not loan:
            return
        if loan["status"] in ("defaulted", "refinanced"):
            return
        total_due = _loan_repayment_total(loan)
        cursor.execute("""
            SELECT COALESCE(SUM(amount), 0)
            FROM payments
            WHERE loan_id = ? AND voided_at IS NULL
        """, (loan_id,))
        total_paid = cursor.fetchone()[0]
        new_status = "paid" if total_paid >= total_due else "active"
        if new_status != loan["status"]:
            cursor.execute("UPDATE loans SET status = ? WHERE id = ?", (new_status, loan_id))
            if new_status == "paid":
                cursor.execute("""
                    UPDATE collateral SET status = 'released'
                    WHERE loan_id = ? AND status = 'pledged'
                """, (loan_id,))

    def _fully_paid_installment_count(self, cursor, loan_id):
        """Count installments whose allocated, non-voided payments cover the amount due."""
        cursor.execute("""
            SELECT COUNT(*)
            FROM (
                SELECT
                    a.id,
                    a.total_due,
                    COALESCE(SUM(
                        CASE WHEN p.voided_at IS NULL THEN pa.amount ELSE 0 END
                    ), 0) AS paid_amount
                FROM amortization_schedule a
                LEFT JOIN payment_allocations pa ON pa.schedule_id = a.id
                LEFT JOIN payments p ON p.id = pa.payment_id
                WHERE a.loan_id = ?
                GROUP BY a.id, a.total_due
                HAVING paid_amount >= a.total_due - 0.005
            ) paid_installments
        """, (int(loan_id),))
        return int(cursor.fetchone()[0])

    def toggle_demo_mode(self, enabled):
        """Toggle demo mode (uses a separate prepopulated database)."""
        enabled = bool(enabled)
        self._is_demo = enabled
        if not enabled:
            load_active_profile()
        set_demo_mode(enabled)
        init_database()
        if enabled:
            try:
                self._ensure_demo_data()
            except Exception as e:
                app_logger.log_exception("toggle_demo_mode > generate_demo_data", e)
                return {"success": False, "demo_active": True, "error": str(e)}
        app_logger.info("Demo mode set to: %s", enabled)
        return {
            "success": True,
            "demo_active": enabled,
            "demo_only": self._demo_only and enabled,
            "demo_edition": self._demo_only,
        }

    def reset_demo_data(self):
        """
        Wipe all demo database tables and regenerate fresh demo data
        (including the alert scenarios with 4 severity levels).
        Safe to call only when demo mode is active.
        """
        if not self._is_demo:
            return {"success": False, "error": "Demo mode must be active to reset demo data."}
        try:
            conn = get_connection()
            c = conn.cursor()
            # Delete in order (foreign keys)
            for table in ['payment_allocations', 'referral_commissions', 'penalties', 'payments',
                          'amortization_schedule', 'loans', 'documents', 'clients']:
                c.execute(f"DELETE FROM {table}")
            # Reset auto-increment sequences
            c.execute("DELETE FROM sqlite_sequence WHERE name IN ('loans','payments','amortization_schedule','penalties','documents','referral_commissions','payment_allocations')")
            conn.commit()
            conn.close()

            # Re-generate fresh scenarios
            import importlib, demo_generator
            importlib.reload(demo_generator)
            demo_generator.generate_demo_data()

            return {"success": True, "message": "Demo data regenerated successfully."}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_demo_status(self):
        """Check if demo mode is active."""
        return self._is_demo

    def get_app_mode(self):
        """Return immutable distribution capabilities for the frontend."""
        return {
            "name": APP_NAME,
            "demo_only": self._is_restricted_demo(),
            "demo_edition": self._demo_only,
            "demo_active": self._is_demo,
        }

    def open_file(self, file_path):
        """Open any existing file or directory natively."""
        if file_path and os.path.exists(file_path):
            return _open_native(file_path)
        return False

    def open_url(self, url):
        """Open a URL (http/https) or mailto: link via the system default app."""
        try:
            if not url or not (url.startswith('http://') or url.startswith('https://') or url.startswith('mailto:')):
                return {"success": False, "error": "Invalid URL"}
            webbrowser.open(url)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ═══════════════════════════════════════════════════════════════
    # DASHBOARD
    # ═══════════════════════════════════════════════════════════════

    def get_dashboard_stats(self):
        """Get summary statistics for the dashboard."""
        conn = get_connection()
        c = conn.cursor()

        # Total capital lent (active loans)
        c.execute("SELECT COALESCE(SUM(principal), 0) FROM loans WHERE status = 'active'")
        active_capital = c.fetchone()[0]

        # Total capital all time
        c.execute("SELECT COALESCE(SUM(principal), 0) FROM loans")
        total_capital = c.fetchone()[0]

        # Total valid payments received.
        c.execute("""
            SELECT COALESCE(SUM(p.amount), 0)
            FROM payments p
            JOIN loans l ON p.loan_id = l.id
            WHERE p.voided_at IS NULL
        """)
        total_collected = c.fetchone()[0]

        # Total expected interest
        c.execute("SELECT COALESCE(SUM(total_interest), 0) FROM loans")
        total_expected_interest = c.fetchone()[0]

        # Interest collected, allocated interest-first within each installment.
        # Subtracting principal only from fully paid loans under-reported active
        # portfolios and could even report zero after substantial collections.
        c.execute("""
            SELECT COALESCE(SUM(
                CASE
                    WHEN schedule_paid >= interest_portion THEN interest_portion
                    ELSE schedule_paid
                END
            ), 0)
            FROM (
                SELECT
                    a.id,
                    a.interest_portion,
                    COALESCE(SUM(
                        CASE WHEN p.voided_at IS NULL THEN pa.amount ELSE 0 END
                    ), 0) AS schedule_paid
                FROM amortization_schedule a
                LEFT JOIN payment_allocations pa ON pa.schedule_id = a.id
                LEFT JOIN payments p ON p.id = pa.payment_id
                GROUP BY a.id, a.interest_portion
            ) allocations
        """)
        interest_collected = c.fetchone()[0]
        c.execute("""
            SELECT COALESCE(SUM(total_interest), 0)
            FROM loans WHERE interest_deducted_upfront = 1
        """)
        upfront_interest_collected = c.fetchone()[0]
        interest_collected = float(interest_collected) + float(upfront_interest_collected)

        c.execute("SELECT COALESCE(SUM(processing_fee + insurance_fee), 0) FROM loans")
        fee_income = float(c.fetchone()[0])
        c.execute("SELECT COALESCE(SUM(disbursed_amount), 0) FROM loans")
        total_disbursed = float(c.fetchone()[0])
        effective_yield = (
            (float(interest_collected) + fee_income) / total_disbursed * 100
            if total_disbursed > 0 else 0
        )
        c.execute("""
            SELECT COALESCE(SUM(taeg * principal), 0), COALESCE(SUM(principal), 0)
            FROM loans WHERE status IN ('active', 'defaulted') AND taeg > 0
        """)
        weighted_taeg, weighted_principal = c.fetchone()
        average_taeg = float(weighted_taeg) / float(weighted_principal) if weighted_principal else 0

        # Client count
        c.execute("SELECT COUNT(*) FROM clients")
        client_count = c.fetchone()[0]

        # Active loans count
        c.execute("SELECT COUNT(*) FROM loans WHERE status = 'active'")
        active_loans = c.fetchone()[0]

        # Defaulted loans count
        c.execute("SELECT COUNT(*) FROM loans WHERE status = 'defaulted'")
        defaulted_loans = c.fetchone()[0]

        # Delinquency rate
        c.execute("SELECT COUNT(*) FROM loans WHERE status IN ('active', 'paid', 'defaulted')")
        total_loans = c.fetchone()[0]
        delinquency_rate = round((defaulted_loans / total_loans * 100) if total_loans > 0 else 0, 1)

        conn.close()

        risk = self.get_portfolio_risk_metrics()

        # Today's unpaid collections only. Paid installments must not remain due.
        today = datetime.now().strftime("%Y-%m-%d")
        today_rows = self.get_collections_by_date(today)
        today_collections = len(today_rows)
        today_amount = sum(row.get("total_due", 0) for row in today_rows)

        return {
            "active_capital": round(active_capital, 2),
            "total_capital": round(total_capital, 2),
            "interest_collected": round(interest_collected, 2),
            "fee_income": round(fee_income, 2),
            "effective_yield": round(effective_yield, 2),
            "average_taeg": round(average_taeg, 2),
            "total_expected_interest": round(total_expected_interest, 2),
            "total_collected": round(total_collected, 2),
            "client_count": client_count,
            "active_loans": active_loans,
            "defaulted_loans": defaulted_loans,
            "delinquency_rate": delinquency_rate,
            "today_collections": today_collections,
            "today_amount": round(today_amount, 2),
            **risk,
        }

    def get_portfolio_risk_metrics(self):
        """Return PAR ratios, aging buckets and post-default recovery metrics."""
        conn = get_connection()
        try:
            c = conn.cursor()
            today = datetime.now().date()
            c.execute("""
                SELECT l.id AS loan_id, l.status, a.id AS schedule_id, a.due_date,
                       a.principal_portion, a.interest_portion, a.total_due,
                       COALESCE(SUM(CASE WHEN p.voided_at IS NULL THEN pa.amount ELSE 0 END), 0) AS allocated
                FROM loans l
                JOIN amortization_schedule a ON a.loan_id = l.id
                LEFT JOIN payment_allocations pa ON pa.schedule_id = a.id
                LEFT JOIN payments p ON p.id = pa.payment_id
                WHERE l.status IN ('active', 'defaulted')
                GROUP BY a.id
                ORDER BY l.id, a.due_date
            """)
            loans = {}
            for row in c.fetchall():
                entry = loans.setdefault(row["loan_id"], {"principal_outstanding": 0.0, "oldest_due": None})
                allocated = min(float(row["allocated"]), float(row["total_due"]))
                interest_paid = min(float(row["interest_portion"]), allocated)
                principal_paid = min(float(row["principal_portion"]), max(0.0, allocated - interest_paid))
                open_principal = max(0.0, float(row["principal_portion"]) - principal_paid)
                entry["principal_outstanding"] += open_principal
                if allocated < float(row["total_due"]) - 0.005:
                    due = datetime.strptime(row["due_date"], "%Y-%m-%d").date()
                    if due < today and (entry["oldest_due"] is None or due < entry["oldest_due"]):
                        entry["oldest_due"] = due

            gross = round(sum(item["principal_outstanding"] for item in loans.values()), 2)
            buckets = {"current": 0.0, "1_30": 0.0, "31_60": 0.0, "61_90": 0.0, "90_plus": 0.0}
            par_amounts = {1: 0.0, 30: 0.0, 60: 0.0, 90: 0.0}
            for item in loans.values():
                amount = item["principal_outstanding"]
                days = (today - item["oldest_due"]).days if item["oldest_due"] else 0
                if days <= 0:
                    buckets["current"] += amount
                elif days <= 30:
                    buckets["1_30"] += amount
                elif days <= 60:
                    buckets["31_60"] += amount
                elif days <= 90:
                    buckets["61_90"] += amount
                else:
                    buckets["90_plus"] += amount
                for threshold in par_amounts:
                    if days >= threshold:
                        par_amounts[threshold] += amount

            c.execute("""
                SELECT l.id, l.balance_at_default,
                       COALESCE(SUM(CASE
                           WHEN p.voided_at IS NULL AND datetime(p.created_at) >= datetime(l.defaulted_at)
                           THEN p.amount ELSE 0 END), 0) AS recovered
                FROM loans l
                LEFT JOIN payments p ON p.loan_id = l.id
                WHERE l.defaulted_at IS NOT NULL AND l.balance_at_default > 0
                GROUP BY l.id
            """)
            defaults = c.fetchall()
            default_balance = sum(float(row["balance_at_default"]) for row in defaults)
            recovered = sum(min(float(row["recovered"]), float(row["balance_at_default"])) for row in defaults)
            recovery_rate = recovered / default_balance * 100 if default_balance > 0 else 0

            return {
                "gross_outstanding_principal": gross,
                "aging_buckets": {key: round(value, 2) for key, value in buckets.items()},
                "par_1": round(par_amounts[1] / gross * 100, 2) if gross else 0,
                "par_30": round(par_amounts[30] / gross * 100, 2) if gross else 0,
                "par_60": round(par_amounts[60] / gross * 100, 2) if gross else 0,
                "par_90": round(par_amounts[90] / gross * 100, 2) if gross else 0,
                "post_default_recovered": round(recovered, 2),
                "post_default_recovery_rate": round(recovery_rate, 2),
            }
        finally:
            conn.close()

    def get_collector_performance(self):
        """Return collection and arrears indicators per assigned collector."""
        conn = get_connection()
        try:
            c = conn.cursor()
            c.execute("""
                SELECT col.id, col.name, col.contact, col.active,
                       COUNT(DISTINCT l.id) AS loan_count,
                       SUM(CASE WHEN l.status = 'active' THEN 1 ELSE 0 END) AS active_loans,
                       COALESCE(SUM(l.principal), 0) AS principal_managed,
                       COALESCE((SELECT SUM(p.amount) FROM payments p
                                 JOIN loans lp ON lp.id = p.loan_id
                                 WHERE lp.collector_id = col.id AND p.voided_at IS NULL), 0) AS collected,
                       COALESCE(AVG(CASE WHEN l.taeg > 0 THEN l.taeg END), 0) AS average_taeg
                FROM collectors col
                LEFT JOIN loans l ON l.collector_id = col.id
                GROUP BY col.id ORDER BY col.active DESC, col.name
            """)
            result = rows_to_list(c.fetchall())
            c.execute("""
                SELECT loan_id, ROUND(SUM(total_due - allocated), 2) AS overdue_amount
                FROM (
                    SELECT a.loan_id, a.total_due,
                           COALESCE(SUM(CASE WHEN p.voided_at IS NULL THEN pa.amount ELSE 0 END), 0) AS allocated
                    FROM amortization_schedule a
                    JOIN loans l ON l.id = a.loan_id
                    LEFT JOIN payment_allocations pa ON pa.schedule_id = a.id
                    LEFT JOIN payments p ON p.id = pa.payment_id
                    WHERE l.status IN ('active', 'defaulted') AND a.due_date < ?
                    GROUP BY a.id
                    HAVING allocated < a.total_due - 0.005
                ) overdue_installments
                GROUP BY loan_id
            """, (datetime.now().strftime("%Y-%m-%d"),))
            overdue_by_loan = {row["loan_id"]: row["overdue_amount"] for row in c.fetchall()}
            c.execute("SELECT id, collector_id FROM loans WHERE collector_id IS NOT NULL")
            collector_by_loan = {row["id"]: row["collector_id"] for row in c.fetchall()}
            overdue_by_collector = {}
            for loan_id, amount in overdue_by_loan.items():
                collector_id = collector_by_loan.get(loan_id)
                if collector_id:
                    overdue_by_collector[collector_id] = overdue_by_collector.get(collector_id, 0) + amount
            for row in result:
                row["overdue_amount"] = round(overdue_by_collector.get(row["id"], 0), 2)
                row["collected"] = round(float(row["collected"] or 0), 2)
                row["principal_managed"] = round(float(row["principal_managed"] or 0), 2)
                row["average_taeg"] = round(float(row["average_taeg"] or 0), 2)
            return result
        finally:
            conn.close()

    # ═══════════════════════════════════════════════════════════════
    # CLIENTS (KYC)
    # ═══════════════════════════════════════════════════════════════

    def get_clients(self, search="", sort="created_at", order="DESC", page=1, per_page=20):
        """Get paginated client list with optional search."""
        conn = get_connection()
        c = conn.cursor()

        allowed_sorts = ['id', 'first_name', 'last_name', 'rating', 'created_at']
        if sort not in allowed_sorts:
            sort = 'created_at'
        order = 'ASC' if order == 'ASC' else 'DESC'

        offset = (page - 1) * per_page

        if search:
            search_param = f"%{search}%"
            c.execute(f"""
                SELECT * FROM clients
                WHERE first_name LIKE ? OR last_name LIKE ? OR id LIKE ? OR contact LIKE ?
                   OR id_number LIKE ? OR employer LIKE ?
                ORDER BY {sort} {order}
                LIMIT ? OFFSET ?
            """, (search_param, search_param, search_param, search_param,
                  search_param, search_param, per_page, offset))
            rows = rows_to_list(c.fetchall())

            c.execute("""
                SELECT COUNT(*) FROM clients
                WHERE first_name LIKE ? OR last_name LIKE ? OR id LIKE ? OR contact LIKE ?
                   OR id_number LIKE ? OR employer LIKE ?
            """, (search_param, search_param, search_param, search_param,
                  search_param, search_param))
        else:
            c.execute(f"SELECT * FROM clients ORDER BY {sort} {order} LIMIT ? OFFSET ?",
                      (per_page, offset))
            rows = rows_to_list(c.fetchall())
            c.execute("SELECT COUNT(*) FROM clients")

        total = c.fetchone()[0]
        conn.close()

        return {
            "clients": rows,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": max(1, -(-total // per_page))
        }

    def get_client(self, client_id):
        """Get a single client with their loans, penalties, referral info, and photo."""
        conn = get_connection()
        c = conn.cursor()

        c.execute("SELECT * FROM clients WHERE id = ?", (client_id,))
        client = dict_from_row(c.fetchone())
        if not client:
            conn.close()
            return None

        # Embed profile photo as base64 for display
        if client.get('photo_path') and os.path.exists(str(client['photo_path'])):
            client['photo_base64'] = self.get_file_as_base64(client['photo_path'])
        else:
            client['photo_base64'] = None

        # Get loans with total_paid
        c.execute("""
            SELECT l.*,
                   (SELECT COALESCE(SUM(amount), 0) FROM payments WHERE loan_id = l.id AND voided_at IS NULL) as total_paid
            FROM loans l WHERE l.client_id = ?
            ORDER BY l.created_at DESC
        """, (client_id,))
        client['loans'] = rows_to_list(c.fetchall())

        # Get referrer info
        if client.get('referred_by'):
            c.execute("SELECT id, first_name, last_name FROM clients WHERE id = ?",
                      (client['referred_by'],))
            client['referrer'] = dict_from_row(c.fetchone())
        else:
            client['referrer'] = None

        # Get people this client referred
        c.execute("SELECT id, first_name, last_name FROM clients WHERE referred_by = ?",
                  (client_id,))
        client['referrals'] = rows_to_list(c.fetchall())

        # Get documents
        c.execute("SELECT * FROM documents WHERE client_id = ? ORDER BY created_at DESC",
                  (client_id,))
        client['documents'] = rows_to_list(c.fetchall())

        # Get penalties
        c.execute("""
            SELECT p.*, l.principal
            FROM penalties p JOIN loans l ON p.loan_id = l.id
            WHERE p.client_id = ? ORDER BY p.penalty_date DESC
        """, (client_id,))
        client['penalties'] = rows_to_list(c.fetchall())

        c.execute("""
            SELECT g.*, l.status AS loan_status
            FROM guarantors g JOIN loans l ON l.id = g.loan_id
            WHERE g.client_id = ? ORDER BY g.created_at DESC
        """, (client_id,))
        client['guarantors'] = rows_to_list(c.fetchall())

        c.execute("""
            SELECT co.*, l.status AS loan_status
            FROM collateral co JOIN loans l ON l.id = co.loan_id
            WHERE co.client_id = ? ORDER BY co.created_at DESC
        """, (client_id,))
        client['collateral'] = rows_to_list(c.fetchall())

        conn.close()
        return client

    def create_client(self, data):
        """Create a new client. Returns the new client ID."""
        conn = get_connection()
        try:
            c = conn.cursor()
            now = datetime.now().isoformat()
            first_name = str(data.get("first_name") or "").strip()
            last_name = str(data.get("last_name") or "").strip()
            if not first_name or not last_name:
                raise ValueError("First name and last name are required.")

            rating = int(data.get("rating", 3))
            if rating < 1 or rating > 5:
                raise ValueError("Client rating must be between 1 and 5.")
            monthly_income = float(data.get("monthly_income") or 0)
            if not math.isfinite(monthly_income) or monthly_income < 0:
                raise ValueError("Monthly income cannot be negative.")
            date_of_birth = str(data.get("date_of_birth") or "").strip()
            if date_of_birth:
                parsed_birth = datetime.strptime(date_of_birth, "%Y-%m-%d")
                if parsed_birth.date() > datetime.now().date():
                    raise ValueError("Date of birth cannot be in the future.")
            gender = str(data.get("gender") or "").strip().lower()
            if gender not in {"", "female", "male", "non_binary", "prefer_not_to_say"}:
                raise ValueError("Invalid gender value.")

            referred_by = data.get("referred_by") or None
            if referred_by:
                c.execute("SELECT id FROM clients WHERE id = ?", (referred_by,))
                if not c.fetchone():
                    raise ValueError("Referring client was not found.")

            client_id = generate_client_id()
            c.execute("""
                INSERT INTO clients
                    (id, first_name, last_name, address, address_detail, contact, email,
                     rating, referred_by, notes, monthly_income, id_number, date_of_birth,
                     employer, occupation, gender, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                client_id,
                first_name,
                last_name,
                str(data.get("address") or "").strip(),
                str(data.get("address_detail") or "").strip(),
                str(data.get("contact") or "").strip(),
                str(data.get("email") or "").strip(),
                rating,
                referred_by,
                str(data.get("notes") or "").strip(),
                monthly_income,
                str(data.get("id_number") or "").strip(),
                date_of_birth,
                str(data.get("employer") or "").strip(),
                str(data.get("occupation") or "").strip(),
                gender,
                now,
                now,
            ))
            self._audit_event(c, "client_created", "client", client_id, {
                "name": f"{first_name} {last_name}"
            })
            conn.commit()
            return client_id
        except (TypeError, ValueError) as e:
            conn.rollback()
            return {"success": False, "error": str(e)}
        except Exception as e:
            conn.rollback()
            app_logger.log_exception("create_client", e)
            return {"success": False, "error": str(e)}
        finally:
            conn.close()

    def update_client(self, client_id, data):
        """Update client details."""
        conn = get_connection()
        try:
            c = conn.cursor()
            data = dict(data or {})
            if "first_name" in data and not str(data["first_name"] or "").strip():
                raise ValueError("First name is required.")
            if "last_name" in data and not str(data["last_name"] or "").strip():
                raise ValueError("Last name is required.")
            if "date_of_birth" in data and data.get("date_of_birth"):
                parsed_birth = datetime.strptime(str(data["date_of_birth"]), "%Y-%m-%d")
                if parsed_birth.date() > datetime.now().date():
                    raise ValueError("Date of birth cannot be in the future.")
            if "gender" in data and str(data.get("gender") or "").lower() not in {
                "", "female", "male", "non_binary", "prefer_not_to_say"
            }:
                raise ValueError("Invalid gender value.")
            if "monthly_income" in data:
                income = float(data.get("monthly_income") or 0)
                if not math.isfinite(income) or income < 0:
                    raise ValueError("Monthly income cannot be negative.")
                data["monthly_income"] = income
            if "rating" in data:
                rating = int(data["rating"])
                if rating < 1 or rating > 5:
                    raise ValueError("Client rating must be between 1 and 5.")
                data["rating"] = rating
            if data.get("referred_by"):
                if data["referred_by"] == client_id:
                    raise ValueError("A client cannot refer themselves.")
                c.execute("SELECT id FROM clients WHERE id = ?", (data["referred_by"],))
                if not c.fetchone():
                    raise ValueError("Referring client was not found.")

            fields = []
            values = []
            allowed = [
                'first_name', 'last_name', 'address', 'address_detail', 'contact', 'email',
                'rating', 'referred_by', 'notes', 'photo_path', 'id_photo_path',
                'monthly_income', 'social_media', 'id_number', 'date_of_birth',
                'employer', 'occupation', 'gender',
            ]
            for key in allowed:
                if key in data:
                    fields.append(f"{key} = ?")
                    value = data[key]
                    values.append(value if value != '' else (None if key == 'referred_by' else ''))
            fields.append("updated_at = ?")
            values.extend([datetime.now().isoformat(), client_id])
            c.execute(f"UPDATE clients SET {', '.join(fields)} WHERE id = ?", values)
            if c.rowcount == 0:
                raise ValueError("Client not found.")
            self._audit_event(c, "client_updated", "client", client_id, {
                "fields": sorted(data.keys())
            })
            conn.commit()
            return True
        except (TypeError, ValueError) as e:
            conn.rollback()
            return {"success": False, "error": str(e)}
        except Exception as e:
            conn.rollback()
            app_logger.log_exception("update_client", e)
            return {"success": False, "error": str(e)}
        finally:
            conn.close()

    def delete_client(self, client_id):
        """Delete a client and all related data."""
        conn = get_connection()
        c = conn.cursor()
        self._audit_event(c, "client_deleted", "client", client_id)
        c.execute("DELETE FROM clients WHERE id = ?", (client_id,))
        conn.commit()
        conn.close()
        return True

    def get_all_clients_simple(self):
        """Get a simple list of all clients (for dropdowns)."""
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT id, first_name, last_name FROM clients ORDER BY first_name")
        result = rows_to_list(c.fetchall())
        conn.close()
        return result

    # ═══════════════════════════════════════════════════════════════
    # LOANS
    # ═══════════════════════════════════════════════════════════════

    def calculate_loan_preview(
        self, principal, rate, interest_type, term_months,
        repayment_frequency="monthly", processing_fee=0, insurance_fee=0,
        interest_deducted_upfront=False, start_date=None,
    ):
        """Preview loan calculations without creating."""
        try:
            return get_loan_summary(
                principal, rate, interest_type, term_months,
                repayment_frequency, processing_fee, insurance_fee,
                bool(interest_deducted_upfront), start_date,
            )
        except ValueError as e:
            return {"success": False, "error": str(e)}

    def create_loan(self, client_id, principal, rate, interest_type, term_months, start_date,
                    rollover_from_loan_id=None, renewal_mode=False,
                    repayment_frequency="monthly", processing_fee=0,
                    insurance_fee=0, interest_deducted_upfront=False,
                    collector_id=None, guarantors=None, collateral=None):
        """
        Create a new loan with full amortization schedule.

        Two refinancing modes:
        - renewal_mode=False (classic rollover): remaining balance of old loan is ADDED
          to the new principal. Client receives extra cash on top.
        - renewal_mode=True (cash-out renewal): 'principal' = total new credit amount.
          The old loan's remaining balance is DEDUCTED from principal to compute the
          net cash given to the client. The loan itself is for the full principal amount.
          Requires at least 3 months paid on the old loan.
        """
        conn = get_connection()
        try:
            c = conn.cursor()
            now = datetime.now().isoformat()

            client_id = str(client_id or "").strip()
            if not client_id:
                raise ValueError("Please select a client before creating a loan.")

            c.execute("SELECT id, referred_by FROM clients WHERE id = ?", (client_id,))
            client = c.fetchone()
            if not client:
                raise ValueError("Client not found. Please select an existing client.")

            new_principal = float(principal)
            rate = float(rate)
            term_months = int(term_months)
            interest_type = str(interest_type or "").strip().lower()
            repayment_frequency = str(repayment_frequency or "monthly").strip().lower()
            processing_fee = float(processing_fee or 0)
            insurance_fee = float(insurance_fee or 0)
            interest_deducted_upfront = bool(interest_deducted_upfront)
            if not math.isfinite(new_principal) or new_principal <= 0:
                raise ValueError("Principal must be greater than zero.")
            if not math.isfinite(rate) or rate < 0:
                raise ValueError("Interest rate cannot be negative.")
            if term_months < 1 or term_months > 120:
                raise ValueError("Loan term must be between 1 and 120 months.")
            if interest_type not in {"fixed", "declining"}:
                raise ValueError("Interest type must be fixed or declining.")
            if repayment_frequency not in {"daily", "weekly", "biweekly", "monthly"}:
                raise ValueError("Invalid repayment frequency.")
            if not math.isfinite(processing_fee) or processing_fee < 0:
                raise ValueError("Processing fee cannot be negative.")
            if not math.isfinite(insurance_fee) or insurance_fee < 0:
                raise ValueError("Insurance fee cannot be negative.")
            datetime.strptime(start_date, "%Y-%m-%d")

            normalized_collector_id = None
            if collector_id not in (None, "", 0, "0"):
                normalized_collector_id = int(collector_id)
                c.execute("SELECT id FROM collectors WHERE id = ? AND active = 1", (normalized_collector_id,))
                if not c.fetchone():
                    raise ValueError("Selected collector was not found or is inactive.")

            rollover_amount = 0.0
            cash_given_to_client = new_principal  # default: full principal is cash
            rollover_id = int(rollover_from_loan_id) if rollover_from_loan_id else None

            # Handle rollover / refinancing
            if rollover_id:
                c.execute(
                    "SELECT principal, total_interest, total_repayment, status FROM loans WHERE id = ? AND client_id = ?",
                    (rollover_id, client_id)
                )
                old_loan = c.fetchone()
                if not old_loan:
                    raise ValueError("Original loan not found for this client.")
                if old_loan["status"] != "active":
                    raise ValueError("Only active loans can be refinanced.")

                paid_count = self._fully_paid_installment_count(c, rollover_id)
                if renewal_mode and paid_count < 3:
                    raise ValueError("Renewal requires at least 3 fully paid installments on the active loan.")

                total_due_old = _loan_repayment_total(old_loan)
                c.execute("SELECT COALESCE(SUM(amount), 0) FROM payments WHERE loan_id = ? AND voided_at IS NULL",
                          (rollover_id,))
                already_paid = c.fetchone()[0]
                rollover_amount = max(0, total_due_old - already_paid)

                if renewal_mode:
                    # RENEWAL MODE: total new credit = principal, client receives the difference.
                    if new_principal < rollover_amount - 0.005:
                        raise ValueError(
                            "New total credit must cover the remaining balance of the current loan."
                        )
                    cash_given_to_client = max(0, new_principal - rollover_amount)
                else:
                    # CLASSIC ROLLOVER: add remaining balance on top of new capital.
                    new_principal += rollover_amount
                    cash_given_to_client = new_principal - rollover_amount

                c.execute("UPDATE loans SET status = 'refinanced' WHERE id = ?", (rollover_id,))

            # Calculate loan
            summary = get_loan_summary(
                new_principal, rate, interest_type, term_months,
                repayment_frequency, processing_fee, insurance_fee,
                interest_deducted_upfront, start_date,
            )
            schedule = generate_amortization_schedule(
                new_principal, rate, interest_type, term_months, start_date,
                repayment_frequency, interest_deducted_upfront,
            )
            if not schedule:
                raise ValueError("Could not generate amortization schedule.")

            # Insert loan
            c.execute("""
                INSERT INTO loans (
                    client_id, principal, interest_rate, interest_type,
                    term_months, original_term_months, start_date, status, total_interest,
                    monthly_payment, original_loan_id, rollover_amount,
                    repayment_frequency, installment_count, installment_amount,
                    processing_fee, insurance_fee, disbursed_amount,
                    interest_deducted_upfront, total_repayment, taeg, collector_id, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, 'active', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                client_id, new_principal, rate, interest_type, term_months, term_months,
                start_date, summary['total_interest'], summary['monthly_payment'],
                rollover_id, rollover_amount, repayment_frequency,
                summary['installment_count'], summary['installment_amount'],
                processing_fee, insurance_fee, summary['disbursed_amount'],
                int(interest_deducted_upfront), summary['total_repayment'],
                summary['taeg'], normalized_collector_id, now,
            ))
            loan_id = c.lastrowid

            # Insert amortization schedule
            for entry in schedule:
                c.execute("""
                    INSERT INTO amortization_schedule
                        (loan_id, month_number, due_date, principal_portion,
                         interest_portion, total_due, balance_remaining)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    loan_id, entry['month_number'], entry['due_date'],
                    entry['principal_portion'], entry['interest_portion'],
                    entry['total_due'], entry['balance_remaining']
                ))

            for item in guarantors or []:
                name = str(item.get("name") or "").strip()
                if not name:
                    continue
                c.execute("""
                    INSERT INTO guarantors
                        (loan_id, client_id, name, contact, relation, id_number,
                         address, notes, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    loan_id, client_id, name, str(item.get("contact") or "").strip(),
                    str(item.get("relation") or "").strip(),
                    str(item.get("id_number") or "").strip(),
                    str(item.get("address") or "").strip(),
                    str(item.get("notes") or "").strip(), now,
                ))

            for item in collateral or []:
                description = str(item.get("description") or "").strip()
                if not description:
                    continue
                collateral_type = str(item.get("collateral_type") or "other").strip().lower()
                if collateral_type not in {"vehicle", "real_estate", "equipment", "jewelry", "electronics", "other"}:
                    raise ValueError("Invalid collateral type.")
                estimated_value = float(item.get("estimated_value") or 0)
                if not math.isfinite(estimated_value) or estimated_value < 0:
                    raise ValueError("Collateral value cannot be negative.")
                c.execute("""
                    INSERT INTO collateral
                        (loan_id, client_id, description, collateral_type,
                         estimated_value, serial_number, plate_number, status, notes, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 'pledged', ?, ?)
                """, (
                    loan_id, client_id, description, collateral_type, estimated_value,
                    str(item.get("serial_number") or "").strip(),
                    str(item.get("plate_number") or "").strip(),
                    str(item.get("notes") or "").strip(), now,
                ))

            # Auto-create referral commission if client was referred
            if client and client['referred_by']:
                c.execute("SELECT key, value FROM settings WHERE key IN ('commission_rate', 'commission_type', 'commission_amount')")
                settings_rows = c.fetchall()
                settings = {r['key']: r['value'] for r in settings_rows}
                commission_type = settings.get('commission_type', 'percentage')
                if commission_type == 'fixed_amount':
                    commission = float(settings.get('commission_amount', '500'))
                else:
                    commission_rate_val = float(settings.get('commission_rate', '2.0'))
                    commission = float(principal) * (commission_rate_val / 100)  # % of new capital only

                c.execute("""
                    INSERT INTO referral_commissions
                        (referrer_id, referred_id, loan_id, commission_amount, status, created_at)
                    VALUES (?, ?, ?, ?, 'pending', ?)
                """, (client['referred_by'], client_id, loan_id, commission, now))

            self._audit_event(c, "loan_created", "loan", loan_id, {
                "client_id": client_id,
                "principal": new_principal,
                "term_months": term_months,
                "interest_type": interest_type,
                "repayment_frequency": repayment_frequency,
                "disbursed_amount": summary["disbursed_amount"],
                "taeg": summary["taeg"],
                "renewal_mode": renewal_mode,
                "rollover_amount": rollover_amount
            })

            conn.commit()
            app_logger.info("Loan created: loan_id=%s client_id=%s principal=%.2f renewal_mode=%s",
                            loan_id, client_id, new_principal, renewal_mode)
            return {
                "success": True,
                "loan_id": loan_id,
                "rollover_amount": rollover_amount,
                "total_principal": new_principal,
                "cash_given_to_client": round(max(
                    0, summary["disbursed_amount"] - (rollover_amount if renewal_mode else 0)
                ), 2),
                "disbursed_amount": summary["disbursed_amount"],
                "total_repayment": summary["total_repayment"],
                "taeg": summary["taeg"],
                "renewal_mode": renewal_mode
            }
        except ValueError as e:
            conn.rollback()
            return {"success": False, "error": str(e)}
        except Exception as e:
            conn.rollback()
            app_logger.log_exception("create_loan", e)
            return {"success": False, "error": str(e)}
        finally:
            conn.close()

    def get_loan(self, loan_id):
        """Get full loan details with schedule and payments."""
        conn = get_connection()
        c = conn.cursor()

        c.execute("""
            SELECT l.*, c.first_name, c.last_name,
                   col.name AS collector_name, col.contact AS collector_contact
            FROM loans l JOIN clients c ON l.client_id = c.id
            LEFT JOIN collectors col ON col.id = l.collector_id
            WHERE l.id = ?
        """, (loan_id,))
        loan = dict_from_row(c.fetchone())
        if not loan:
            conn.close()
            return None

        # Amortization schedule
        c.execute("""
            SELECT a.*,
                   COALESCE(SUM(CASE WHEN p.voided_at IS NULL THEN pa.amount ELSE 0 END), 0) AS allocated
            FROM amortization_schedule a
            LEFT JOIN payment_allocations pa ON pa.schedule_id = a.id
            LEFT JOIN payments p ON p.id = pa.payment_id
            WHERE a.loan_id = ?
            GROUP BY a.id ORDER BY a.month_number
        """, (loan_id,))
        loan['schedule'] = rows_to_list(c.fetchall())

        # Payments
        c.execute("SELECT * FROM payments WHERE loan_id = ? AND voided_at IS NULL ORDER BY payment_date DESC",
                  (loan_id,))
        loan['payments'] = rows_to_list(c.fetchall())

        # Total paid
        c.execute("SELECT COALESCE(SUM(amount), 0) FROM payments WHERE loan_id = ? AND voided_at IS NULL", (loan_id,))
        loan['total_paid'] = c.fetchone()[0]
        loan['remaining'] = max(0, round(_loan_repayment_total(loan) - loan['total_paid'], 2))

        c.execute("SELECT * FROM guarantors WHERE loan_id = ? ORDER BY created_at", (loan_id,))
        loan['guarantors'] = rows_to_list(c.fetchall())
        c.execute("SELECT * FROM collateral WHERE loan_id = ? ORDER BY created_at", (loan_id,))
        loan['collateral'] = rows_to_list(c.fetchall())

        conn.close()
        return loan

    def get_client_loans(self, client_id):
        """Get all loans for a client."""
        conn = get_connection()
        c = conn.cursor()
        c.execute("""
            SELECT l.*,
                   (SELECT COALESCE(SUM(amount), 0) FROM payments WHERE loan_id = l.id AND voided_at IS NULL) as total_paid
            FROM loans l WHERE l.client_id = ?
            ORDER BY l.created_at DESC
        """, (client_id,))
        result = rows_to_list(c.fetchall())
        conn.close()
        return result

    def get_all_loans(self, status="all", search="", page=1, per_page=20):
        """Get all loans with pagination."""
        conn = get_connection()
        c = conn.cursor()
        offset = (page - 1) * per_page

        where_clauses = []
        params = []

        if status != "all":
            where_clauses.append("l.status = ?")
            params.append(status)

        if search:
            where_clauses.append(
                "(c.first_name LIKE ? OR c.last_name LIKE ? OR c.id LIKE ?)")
            params.extend([f"%{search}%"] * 3)

        where = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

        c.execute(f"""
            SELECT l.*, c.first_name, c.last_name,
                   (SELECT COALESCE(SUM(amount), 0) FROM payments WHERE loan_id = l.id AND voided_at IS NULL) as total_paid
            FROM loans l
            JOIN clients c ON l.client_id = c.id
            {where}
            ORDER BY l.created_at DESC LIMIT ? OFFSET ?
        """, params + [per_page, offset])
        loans = rows_to_list(c.fetchall())

        c.execute(f"""
            SELECT COUNT(*) FROM loans l
            JOIN clients c ON l.client_id = c.id {where}
        """, params)
        total = c.fetchone()[0]

        conn.close()
        return {
            "loans": loans,
            "total": total,
            "page": page,
            "total_pages": max(1, -(-total // per_page))
        }

    def update_loan_status(self, loan_id, status):
        """Update a loan's status."""
        normalized_status = str(status or "").strip().lower()
        if normalized_status not in {"active", "paid", "defaulted", "refinanced"}:
            return {"success": False, "error": "Invalid loan status."}
        conn = get_connection()
        try:
            c = conn.cursor()
            c.execute("SELECT * FROM loans WHERE id = ?", (int(loan_id),))
            loan = c.fetchone()
            if not loan:
                return {"success": False, "error": "Loan not found."}
            if normalized_status == "defaulted" and loan["status"] != "defaulted":
                c.execute("""
                    SELECT COALESCE(SUM(amount), 0) FROM payments
                    WHERE loan_id = ? AND voided_at IS NULL
                """, (int(loan_id),))
                paid = float(c.fetchone()[0])
                balance = max(0, round(_loan_repayment_total(loan) - paid, 2))
                c.execute("""
                    UPDATE loans
                    SET status = 'defaulted', defaulted_at = ?, balance_at_default = ?
                    WHERE id = ?
                """, (datetime.now().isoformat(), balance, int(loan_id)))
            else:
                c.execute("""
                    UPDATE loans
                    SET status = ?,
                        defaulted_at = CASE WHEN ? = 'defaulted' THEN defaulted_at ELSE NULL END,
                        balance_at_default = CASE WHEN ? = 'defaulted' THEN balance_at_default ELSE 0 END
                    WHERE id = ?
                """, (normalized_status, normalized_status, normalized_status, int(loan_id)))
            if normalized_status == "paid":
                c.execute("""
                    UPDATE collateral SET status = 'released'
                    WHERE loan_id = ? AND status = 'pledged'
                """, (int(loan_id),))
            self._audit_event(c, "loan_status_changed", "loan", loan_id, {
                "status": normalized_status
            })
            conn.commit()
            return {"success": True, "status": normalized_status}
        except (TypeError, ValueError):
            conn.rollback()
            return {"success": False, "error": "Invalid loan identifier."}
        finally:
            conn.close()

    def extend_loan(self, loan_id, additional_months):
        """
        Extend an active loan by spreading its unpaid principal and interest
        across the remaining installments plus the requested extra months.

        The contractual total is preserved: extending a term never adds a
        hidden second interest charge and existing payment allocations remain
        attached to their original installments.
        """
        conn = get_connection()
        try:
            c = conn.cursor()
            loan_id = int(loan_id)
            additional_months = int(additional_months)
            if additional_months < 1 or additional_months > 60:
                return {"success": False, "error": "Additional months must be between 1 and 60."}

            # Get loan details
            c.execute("SELECT * FROM loans WHERE id = ?", (loan_id,))
            loan = dict_from_row(c.fetchone())
            if not loan:
                return {"success": False, "error": "Loan not found"}

            if loan['status'] != 'active':
                return {"success": False, "error": "Only active loans can be extended"}

            c.execute("""
                SELECT
                    a.*,
                    COALESCE(SUM(
                        CASE WHEN p.voided_at IS NULL THEN pa.amount ELSE 0 END
                    ), 0) AS allocated
                FROM amortization_schedule a
                LEFT JOIN payment_allocations pa ON pa.schedule_id = a.id
                LEFT JOIN payments p ON p.id = pa.payment_id
                WHERE a.loan_id = ?
                GROUP BY a.id
                ORDER BY a.month_number
            """, (loan_id,))
            schedule_rows = rows_to_list(c.fetchall())
            if not schedule_rows:
                return {"success": False, "error": "Loan has no amortization schedule."}

            open_rows = [
                row for row in schedule_rows
                if float(row["allocated"]) < float(row["total_due"]) - 0.005
            ]
            if not open_rows:
                return {"success": False, "error": "Loan is already fully paid."}

            remaining_principal = 0.0
            remaining_interest = 0.0
            paid_components = {}
            for row in open_rows:
                allocated = min(float(row["allocated"]), float(row["total_due"]))
                interest_paid = min(float(row["interest_portion"]), allocated)
                principal_paid = min(
                    float(row["principal_portion"]),
                    max(0.0, allocated - interest_paid)
                )
                paid_components[row["id"]] = (principal_paid, interest_paid)
                remaining_principal += float(row["principal_portion"]) - principal_paid
                remaining_interest += float(row["interest_portion"]) - interest_paid

            frequency = str(loan.get("repayment_frequency") or "monthly")
            added_installments = get_installment_count(additional_months, frequency)
            installment_count = len(open_rows) + added_installments
            principal_parts = distribute_money(remaining_principal, installment_count)
            interest_parts = distribute_money(remaining_interest, installment_count)

            # Rebalance existing unpaid rows while retaining their IDs and allocations.
            for index, row in enumerate(open_rows):
                paid_principal, paid_interest = paid_components[row["id"]]
                principal_portion = round(paid_principal + principal_parts[index], 2)
                interest_portion = round(paid_interest + interest_parts[index], 2)
                c.execute("""
                    UPDATE amortization_schedule
                    SET principal_portion = ?, interest_portion = ?, total_due = ?
                    WHERE id = ?
                """, (
                    principal_portion,
                    interest_portion,
                    round(principal_portion + interest_portion, 2),
                    row["id"]
                ))

            last_due_date = datetime.strptime(schedule_rows[-1]["due_date"], "%Y-%m-%d")
            last_month_num = int(schedule_rows[-1]["month_number"])
            for offset in range(added_installments):
                part_index = len(open_rows) + offset
                due_date = advance_due_date(last_due_date, offset + 1, frequency)
                c.execute("""
                    INSERT INTO amortization_schedule
                        (loan_id, month_number, due_date, principal_portion,
                         interest_portion, total_due, balance_remaining)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    loan_id,
                    last_month_num + offset + 1,
                    due_date.strftime("%Y-%m-%d"),
                    principal_parts[part_index],
                    interest_parts[part_index],
                    round(principal_parts[part_index] + interest_parts[part_index], 2),
                    0
                ))

            # Recompute principal balances from the complete revised schedule.
            c.execute("""
                SELECT id, principal_portion
                FROM amortization_schedule
                WHERE loan_id = ?
                ORDER BY month_number
            """, (loan_id,))
            principal_balance = round(float(loan["principal"]), 2)
            for row in c.fetchall():
                principal_balance = max(0, round(principal_balance - row["principal_portion"], 2))
                c.execute(
                    "UPDATE amortization_schedule SET balance_remaining = ? WHERE id = ?",
                    (principal_balance, row["id"])
                )

            new_term = int(loan['term_months']) + additional_months
            new_installment = round(principal_parts[0] + interest_parts[0], 2)
            c.execute("""
                UPDATE loans
                SET term_months = ?, monthly_payment = ?, installment_amount = ?,
                    installment_count = installment_count + ?
                WHERE id = ?
            """, (new_term, new_installment, new_installment, added_installments, loan_id))

            c.execute("""
                SELECT ROUND(COALESCE(SUM(total_due), 0), 2)
                FROM amortization_schedule
                WHERE loan_id = ?
            """, (loan_id,))
            schedule_total = float(c.fetchone()[0])
            contract_total = _loan_repayment_total(loan)
            if abs(schedule_total - contract_total) > 0.01:
                raise ValueError("Extended schedule does not reconcile with the loan total.")

            self._audit_event(c, "loan_extended", "loan", loan_id, {
                "additional_months": additional_months,
                "added_installments": added_installments,
                "new_term": new_term,
                "new_installment": new_installment,
                "contract_total": contract_total
            })
            conn.commit()
            app_logger.info("Loan extended: loan_id=%s added %d months", loan_id, additional_months)
            return {
                "success": True,
                "new_term": new_term,
                "additional_months": additional_months,
                "new_monthly_payment": new_installment,
                "remaining_balance": round(remaining_principal + remaining_interest, 2)
            }
        except ValueError as e:
            conn.rollback()
            return {"success": False, "error": str(e)}
        except Exception as e:
            conn.rollback()
            app_logger.log_exception("extend_loan", e)
            return {"success": False, "error": str(e)}
        finally:
            conn.close()

    def get_monthly_earnings(self):
        """
        Returns total payments collected grouped by month (YYYY-MM).
        Also returns interest earned estimate per month.
        """
        conn = get_connection()
        c = conn.cursor()
        c.execute("""
            SELECT
                strftime('%Y-%m', p.payment_date) AS month,
                COUNT(p.id) AS payment_count,
                SUM(p.amount) AS total_collected,
                COUNT(DISTINCT l.client_id) AS unique_clients
            FROM payments p
            JOIN loans l ON p.loan_id = l.id
            WHERE p.voided_at IS NULL
            GROUP BY month
            ORDER BY month DESC
            LIMIT 24
        """)
        rows = rows_to_list(c.fetchall())
        conn.close()
        return rows

    def get_all_payments_detailed(self, limit=500):
        """
        Returns all payments with detailed loan and client info:
        - amount paid, date
        - loan principal, term, monthly payment
        - months remaining, total remaining balance
        """
        conn = get_connection()
        c = conn.cursor()
        c.execute("""
            SELECT
                p.id AS payment_id,
                p.amount,
                p.payment_date,
                p.payment_method,
                p.notes,
                l.id AS loan_id,
                l.principal,
                l.term_months,
                l.monthly_payment,
                l.interest_rate,
                l.interest_type,
                l.start_date,
                l.status AS loan_status,
                l.total_interest,
                l.total_repayment,
                c.id AS client_id,
                c.first_name,
                c.last_name,
                (SELECT COALESCE(SUM(amount), 0) FROM payments WHERE loan_id = l.id AND voided_at IS NULL) AS total_paid_on_loan,
                (
                    SELECT COUNT(*)
                    FROM amortization_schedule a2
                    WHERE a2.loan_id = l.id
                      AND COALESCE((
                          SELECT SUM(pa2.amount)
                          FROM payment_allocations pa2
                          JOIN payments p2 ON p2.id = pa2.payment_id
                          WHERE pa2.schedule_id = a2.id
                            AND p2.voided_at IS NULL
                      ), 0) >= a2.total_due - 0.005
                ) AS installments_paid
            FROM payments p
            JOIN loans l ON p.loan_id = l.id
            JOIN clients c ON l.client_id = c.id
            WHERE p.voided_at IS NULL
            ORDER BY p.payment_date DESC, p.id DESC
            LIMIT ?
        """, (int(limit),))
        rows = rows_to_list(c.fetchall())
        conn.close()

        # Enrich with computed fields
        for r in rows:
            total_due = _loan_repayment_total(r)
            remaining = max(0, total_due - r['total_paid_on_loan'])
            months_paid = int(r['installments_paid'] or 0)
            months_remaining = max(0, r['term_months'] - months_paid)
            r['total_due'] = round(total_due, 2)
            r['remaining_balance'] = round(remaining, 2)
            r['months_paid'] = months_paid
            r['months_remaining'] = months_remaining
        return rows

    def _get_unpaid_collection_rows(self, extra_where="", params=(), order_by="a.due_date ASC, cl.last_name ASC"):
        """
        Return scheduled collection rows that are still unpaid.
        Payments are not linked to a specific installment, so coverage is computed
        cumulatively: an installment is due only when total_paid < cumulative_due.
        """
        conn = get_connection()
        try:
            c = conn.cursor()
            c.execute(f"""
            SELECT DISTINCT
                a.*,
                l.client_id,
                l.principal,
                l.monthly_payment,
                l.term_months,
                l.status AS loan_status,
                cl.first_name,
                cl.last_name,
                cl.contact,
                cl.email,
                COALESCE((SELECT SUM(amount) FROM payments WHERE loan_id = l.id AND voided_at IS NULL), 0) AS total_paid,
                COALESCE((
                    SELECT SUM(pa.amount)
                    FROM payment_allocations pa
                    JOIN payments p ON p.id = pa.payment_id
                    WHERE pa.schedule_id = a.id
                      AND p.voided_at IS NULL
                ), 0) AS schedule_paid
            FROM amortization_schedule a
            JOIN loans l ON a.loan_id = l.id
            JOIN clients cl ON l.client_id = cl.id
            WHERE 1 = 1
              {extra_where}
              AND l.status = 'active'
              AND COALESCE((
                    SELECT SUM(pa.amount)
                    FROM payment_allocations pa
                    JOIN payments p ON p.id = pa.payment_id
                    WHERE pa.schedule_id = a.id
                      AND p.voided_at IS NULL
              ), 0) < a.total_due
            ORDER BY {order_by}
        """, tuple(params))
            rows = rows_to_list(c.fetchall())
        finally:
            conn.close()

        for row in rows:
            outstanding_for_schedule = max(0, row["total_due"] - row["schedule_paid"])
            row["scheduled_total_due"] = row["total_due"]
            row["total_due"] = round(outstanding_for_schedule, 2)
        return rows

    def get_collections_by_day_of_month(self, day_of_month):
        """
        Returns active loans that still have an unpaid installment on a specific day.
        """
        day = int(day_of_month)
        return self._get_unpaid_collection_rows(
            "AND CAST(strftime('%d', a.due_date) AS INTEGER) = ?",
            (day,),
            "a.due_date ASC, cl.last_name ASC"
        )

    def record_payment_for_schedule(self, loan_id, amount, method, payment_date, notes=""):
        """Alias for record_payment — used by collections validation."""
        return self.record_payment(loan_id, amount, method, payment_date, notes)

    # ═══════════════════════════════════════════════════════════════
    # PAYMENTS
    # ═══════════════════════════════════════════════════════════════

    def record_payment(self, loan_id, amount, method, payment_date, notes=""):
        """Record a payment for a loan."""
        conn = get_connection()
        try:
            c = conn.cursor()
            now = datetime.now().isoformat()
            loan_id = int(loan_id)
            amount = float(amount)
            method = _normalize_payment_method(method)
            if not math.isfinite(amount) or amount <= 0:
                raise ValueError("Payment amount must be greater than zero.")
            datetime.strptime(payment_date, "%Y-%m-%d")

            # Check the loan and outstanding balance before inserting.
            c.execute(
                "SELECT principal, total_interest, total_repayment, status FROM loans WHERE id = ?",
                (loan_id,)
            )
            loan = c.fetchone()
            if not loan:
                raise ValueError("Loan not found.")
            if loan["status"] in {"paid", "refinanced"}:
                raise ValueError(f"Payments cannot be recorded on a {loan['status']} loan.")

            c.execute("""
                SELECT COALESCE(SUM(amount), 0)
                FROM payments
                WHERE loan_id = ? AND voided_at IS NULL
            """, (loan_id,))
            already_paid = float(c.fetchone()[0])
            outstanding = max(0, round(_loan_repayment_total(loan) - already_paid, 2))
            if outstanding <= 0:
                raise ValueError("Loan is already fully paid.")
            if amount > outstanding + 0.005:
                raise ValueError(
                    f"Payment exceeds the outstanding balance of {outstanding:,.2f}."
                )

            c.execute("""
                INSERT INTO payments (loan_id, amount, payment_date, payment_method, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (loan_id, amount, payment_date, method, notes, now))
            payment_id = c.lastrowid  # Capture IMMEDIATELY after INSERT before any SELECT
            self._allocate_payment(c, loan_id, payment_id, amount)

            c.execute(
                "SELECT COALESCE(SUM(amount), 0) FROM payment_allocations WHERE payment_id = ?",
                (payment_id,)
            )
            allocated = float(c.fetchone()[0])
            if abs(allocated - amount) > 0.01:
                raise ValueError("Payment could not be fully allocated to the loan schedule.")

            self._recompute_loan_status(c, loan_id)
            self._audit_event(c, "payment_recorded", "payment", payment_id, {
                "loan_id": loan_id,
                "amount": amount,
                "method": method,
                "payment_date": payment_date
            })

            conn.commit()
            app_logger.info("Payment recorded: payment_id=%s loan_id=%s amount=%.2f method=%s",
                            payment_id, loan_id, amount, method)
            return payment_id
        except ValueError as e:
            conn.rollback()
            return {"success": False, "error": str(e)}
        except Exception as e:
            conn.rollback()
            app_logger.log_exception("record_payment", e)
            return {"success": False, "error": str(e)}
        finally:
            conn.close()

    def void_payment(self, payment_id, reason=""):
        """
        Void a payment without deleting the original row.
        Allocations stay linked but are ignored because the payment is voided.
        """
        conn = get_connection()
        try:
            c = conn.cursor()
            payment_id = int(payment_id)
            reason = str(reason or "").strip()
            if len(reason) < 3:
                return {"success": False, "error": "Void reason is required."}

            c.execute("""
                SELECT id, loan_id, amount, voided_at
                FROM payments
                WHERE id = ?
            """, (payment_id,))
            payment = c.fetchone()
            if not payment:
                return {"success": False, "error": "Payment not found."}
            if payment["voided_at"]:
                return {"success": False, "error": "Payment is already voided."}

            now = datetime.now().isoformat()
            c.execute("""
                UPDATE payments
                SET voided_at = ?, void_reason = ?
                WHERE id = ?
            """, (now, reason, payment_id))
            self._recompute_loan_status(c, payment["loan_id"])
            self._audit_event(c, "payment_voided", "payment", payment_id, {
                "loan_id": payment["loan_id"],
                "amount": payment["amount"],
                "reason": reason
            })
            conn.commit()
            return {"success": True}
        except Exception as e:
            conn.rollback()
            app_logger.log_exception("void_payment", e)
            return {"success": False, "error": str(e)}
        finally:
            conn.close()

    def get_payments(self, loan_id):
        """Get all payments for a loan."""
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM payments WHERE loan_id = ? AND voided_at IS NULL ORDER BY payment_date DESC",
                  (loan_id,))
        result = rows_to_list(c.fetchall())
        conn.close()
        return result

    def get_recent_payments(self, limit=10):
        """Get recent payments across all loans."""
        conn = get_connection()
        c = conn.cursor()
        c.execute("""
            SELECT p.*, c.first_name, c.last_name, c.id as client_id
            FROM payments p
            JOIN loans l ON p.loan_id = l.id
            JOIN clients c ON l.client_id = c.id
            WHERE p.voided_at IS NULL
            ORDER BY p.created_at DESC LIMIT ?
        """, (limit,))
        result = rows_to_list(c.fetchall())
        conn.close()
        return result

    # ═══════════════════════════════════════════════════════════════
    # COLLECTION CALENDAR
    # ═══════════════════════════════════════════════════════════════

    def get_today_collections(self):
        """Get all collections due today."""
        today = datetime.now().strftime("%Y-%m-%d")
        return self.get_collections_by_date(today)

    def get_collections_by_date(self, date):
        """Get all collections due on a specific date."""
        return self._get_unpaid_collection_rows(
            "AND a.due_date = ?",
            (date,),
            "cl.last_name ASC"
        )

    def get_collections_range(self, start_date, end_date):
        """Get collections for a date range (for calendar view)."""
        rows = self._get_unpaid_collection_rows(
            "AND a.due_date BETWEEN ? AND ?",
            (start_date, end_date),
            "a.due_date ASC"
        )
        grouped = {}
        for row in rows:
            day = row["due_date"]
            if day not in grouped:
                grouped[day] = {"due_date": day, "count": 0, "total_amount": 0}
            grouped[day]["count"] += 1
            grouped[day]["total_amount"] += row.get("total_due", 0)
        return [
            {
                "due_date": value["due_date"],
                "count": value["count"],
                "total_amount": round(value["total_amount"], 2)
            }
            for value in sorted(grouped.values(), key=lambda item: item["due_date"])
        ]

    # ═══════════════════════════════════════════════════════════════
    # GUARANTORS, COLLATERAL & COLLECTORS
    # ═══════════════════════════════════════════════════════════════

    def add_guarantor(self, loan_id, data):
        conn = get_connection()
        try:
            c = conn.cursor()
            loan_id = int(loan_id)
            c.execute("SELECT client_id FROM loans WHERE id = ?", (loan_id,))
            loan = c.fetchone()
            if not loan:
                raise ValueError("Loan not found.")
            name = str((data or {}).get("name") or "").strip()
            if not name:
                raise ValueError("Guarantor name is required.")
            now = datetime.now().isoformat()
            c.execute("""
                INSERT INTO guarantors
                    (loan_id, client_id, name, contact, relation, id_number,
                     address, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                loan_id, loan["client_id"], name,
                str(data.get("contact") or "").strip(),
                str(data.get("relation") or "").strip(),
                str(data.get("id_number") or "").strip(),
                str(data.get("address") or "").strip(),
                str(data.get("notes") or "").strip(), now,
            ))
            guarantor_id = c.lastrowid
            self._audit_event(c, "guarantor_added", "guarantor", guarantor_id, {"loan_id": loan_id})
            conn.commit()
            return {"success": True, "id": guarantor_id}
        except (TypeError, ValueError) as e:
            conn.rollback()
            return {"success": False, "error": str(e)}
        finally:
            conn.close()

    def update_guarantor(self, guarantor_id, data):
        allowed = {"name", "contact", "relation", "id_number", "address", "notes"}
        fields = []
        values = []
        for key in allowed:
            if key in (data or {}):
                value = str(data.get(key) or "").strip()
                if key == "name" and not value:
                    return {"success": False, "error": "Guarantor name is required."}
                fields.append(f"{key} = ?")
                values.append(value)
        if not fields:
            return {"success": False, "error": "No guarantor fields to update."}
        conn = get_connection()
        try:
            c = conn.cursor()
            values.append(int(guarantor_id))
            c.execute(f"UPDATE guarantors SET {', '.join(fields)} WHERE id = ?", values)
            if c.rowcount == 0:
                raise ValueError("Guarantor not found.")
            self._audit_event(c, "guarantor_updated", "guarantor", guarantor_id)
            conn.commit()
            return {"success": True}
        except (TypeError, ValueError) as e:
            conn.rollback()
            return {"success": False, "error": str(e)}
        finally:
            conn.close()

    def delete_guarantor(self, guarantor_id):
        conn = get_connection()
        try:
            c = conn.cursor()
            c.execute("SELECT signature_path FROM guarantors WHERE id = ?", (int(guarantor_id),))
            row = c.fetchone()
            if not row:
                return {"success": False, "error": "Guarantor not found."}
            c.execute("DELETE FROM guarantors WHERE id = ?", (int(guarantor_id),))
            self._audit_event(c, "guarantor_deleted", "guarantor", guarantor_id)
            conn.commit()
            signature_path = row["signature_path"] or ""
            if signature_path and os.path.isfile(signature_path):
                try:
                    os.remove(signature_path)
                except OSError:
                    app_logger.warning("Could not delete guarantor signature: %s", signature_path)
            return {"success": True}
        finally:
            conn.close()

    def save_guarantor_signature(self, guarantor_id, base64_data):
        try:
            guarantor_id = int(guarantor_id)
            conn = get_connection()
            try:
                row = conn.execute(
                    "SELECT signature_path FROM guarantors WHERE id = ?", (guarantor_id,)
                ).fetchone()
            finally:
                conn.close()
            if not row:
                raise ValueError("Guarantor not found.")
            old_signature = row["signature_path"] or ""
            raw = str(base64_data or "")
            if not raw:
                raise ValueError("Signature data is required.")
            image = base64.b64decode(raw.split(",")[-1], validate=True)
            if not image or len(image) > 5 * 1024 * 1024:
                raise ValueError("Invalid or oversized signature image.")
            signatures_dir = os.path.join(MEDIA_DIR, "signatures")
            os.makedirs(signatures_dir, exist_ok=True)
            filepath = os.path.join(signatures_dir, f"guarantor_{guarantor_id}_{int(datetime.now().timestamp())}.png")
            with open(filepath, "wb") as handle:
                handle.write(image)
            conn = get_connection()
            try:
                c = conn.cursor()
                c.execute("UPDATE guarantors SET signature_path = ? WHERE id = ?", (filepath, guarantor_id))
                self._audit_event(c, "guarantor_signature_saved", "guarantor", guarantor_id)
                conn.commit()
            finally:
                conn.close()
            if old_signature and old_signature != filepath and os.path.isfile(old_signature):
                try:
                    os.remove(old_signature)
                except OSError:
                    app_logger.warning("Could not replace guarantor signature: %s", old_signature)
            return {"success": True, "path": filepath}
        except (TypeError, ValueError, binascii.Error) as e:
            return {"success": False, "error": str(e)}

    def add_collateral(self, loan_id, data):
        conn = get_connection()
        try:
            c = conn.cursor()
            loan_id = int(loan_id)
            c.execute("SELECT client_id FROM loans WHERE id = ?", (loan_id,))
            loan = c.fetchone()
            if not loan:
                raise ValueError("Loan not found.")
            description = str((data or {}).get("description") or "").strip()
            if not description:
                raise ValueError("Collateral description is required.")
            kind = str(data.get("collateral_type") or "other").strip().lower()
            valid_types = {"vehicle", "real_estate", "equipment", "jewelry", "electronics", "other"}
            if kind not in valid_types:
                raise ValueError("Invalid collateral type.")
            value = float(data.get("estimated_value") or 0)
            if not math.isfinite(value) or value < 0:
                raise ValueError("Collateral value cannot be negative.")
            now = datetime.now().isoformat()
            c.execute("""
                INSERT INTO collateral
                    (loan_id, client_id, description, collateral_type, estimated_value,
                     serial_number, plate_number, status, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'pledged', ?, ?)
            """, (
                loan_id, loan["client_id"], description, kind, value,
                str(data.get("serial_number") or "").strip(),
                str(data.get("plate_number") or "").strip(),
                str(data.get("notes") or "").strip(), now,
            ))
            collateral_id = c.lastrowid
            self._audit_event(c, "collateral_added", "collateral", collateral_id, {"loan_id": loan_id})
            conn.commit()
            return {"success": True, "id": collateral_id}
        except (TypeError, ValueError) as e:
            conn.rollback()
            return {"success": False, "error": str(e)}
        finally:
            conn.close()

    def update_collateral(self, collateral_id, data):
        allowed = {"description", "collateral_type", "estimated_value", "serial_number", "plate_number", "status", "notes"}
        fields = []
        values = []
        valid_statuses = {"pledged", "released", "seized", "sold"}
        valid_types = {"vehicle", "real_estate", "equipment", "jewelry", "electronics", "other"}
        try:
            for key in allowed:
                if key not in (data or {}):
                    continue
                value = data.get(key)
                if key == "estimated_value":
                    value = float(value or 0)
                    if not math.isfinite(value) or value < 0:
                        raise ValueError("Collateral value cannot be negative.")
                else:
                    value = str(value or "").strip()
                if key == "description" and not value:
                    raise ValueError("Collateral description is required.")
                if key == "status" and value not in valid_statuses:
                    raise ValueError("Invalid collateral status.")
                if key == "collateral_type" and value not in valid_types:
                    raise ValueError("Invalid collateral type.")
                fields.append(f"{key} = ?")
                values.append(value)
        except (TypeError, ValueError) as e:
            return {"success": False, "error": str(e)}
        if not fields:
            return {"success": False, "error": "No collateral fields to update."}
        conn = get_connection()
        try:
            c = conn.cursor()
            values.append(int(collateral_id))
            c.execute(f"UPDATE collateral SET {', '.join(fields)} WHERE id = ?", values)
            if c.rowcount == 0:
                raise ValueError("Collateral not found.")
            self._audit_event(c, "collateral_updated", "collateral", collateral_id)
            conn.commit()
            return {"success": True}
        except (TypeError, ValueError) as e:
            conn.rollback()
            return {"success": False, "error": str(e)}
        finally:
            conn.close()

    def delete_collateral(self, collateral_id):
        conn = get_connection()
        try:
            c = conn.cursor()
            c.execute("DELETE FROM collateral WHERE id = ?", (int(collateral_id),))
            if c.rowcount == 0:
                return {"success": False, "error": "Collateral not found."}
            self._audit_event(c, "collateral_deleted", "collateral", collateral_id)
            conn.commit()
            return {"success": True}
        finally:
            conn.close()

    def get_collectors(self, active_only=False):
        conn = get_connection()
        try:
            query = "SELECT * FROM collectors"
            params = ()
            if active_only:
                query += " WHERE active = 1"
            query += " ORDER BY active DESC, name"
            return rows_to_list(conn.execute(query, params).fetchall())
        finally:
            conn.close()

    def add_collector(self, data):
        name = str((data or {}).get("name") or "").strip()
        if not name:
            return {"success": False, "error": "Collector name is required."}
        conn = get_connection()
        try:
            c = conn.cursor()
            c.execute("""
                INSERT INTO collectors (name, contact, active, notes, created_at)
                VALUES (?, ?, 1, ?, ?)
            """, (name, str(data.get("contact") or "").strip(),
                  str(data.get("notes") or "").strip(), datetime.now().isoformat()))
            collector_id = c.lastrowid
            self._audit_event(c, "collector_added", "collector", collector_id)
            conn.commit()
            return {"success": True, "id": collector_id}
        finally:
            conn.close()

    def update_collector(self, collector_id, data):
        name = str((data or {}).get("name") or "").strip()
        if not name:
            return {"success": False, "error": "Collector name is required."}
        conn = get_connection()
        try:
            c = conn.cursor()
            c.execute("""
                UPDATE collectors SET name = ?, contact = ?, active = ?, notes = ? WHERE id = ?
            """, (name, str(data.get("contact") or "").strip(),
                  int(bool(data.get("active", True))), str(data.get("notes") or "").strip(),
                  int(collector_id)))
            if c.rowcount == 0:
                return {"success": False, "error": "Collector not found."}
            self._audit_event(c, "collector_updated", "collector", collector_id)
            conn.commit()
            return {"success": True}
        finally:
            conn.close()

    def assign_loan_collector(self, loan_id, collector_id=None):
        conn = get_connection()
        try:
            c = conn.cursor()
            loan_id = int(loan_id)
            normalized = None
            if collector_id not in (None, "", 0, "0"):
                normalized = int(collector_id)
                c.execute("SELECT id FROM collectors WHERE id = ? AND active = 1", (normalized,))
                if not c.fetchone():
                    raise ValueError("Collector not found or inactive.")
            c.execute("UPDATE loans SET collector_id = ? WHERE id = ?", (normalized, loan_id))
            if c.rowcount == 0:
                raise ValueError("Loan not found.")
            self._audit_event(c, "loan_collector_assigned", "loan", loan_id, {"collector_id": normalized})
            conn.commit()
            return {"success": True, "collector_id": normalized}
        except (TypeError, ValueError) as e:
            conn.rollback()
            return {"success": False, "error": str(e)}
        finally:
            conn.close()

    # ═══════════════════════════════════════════════════════════════
    # DOCUMENTS & MEDIA
    # ═══════════════════════════════════════════════════════════════

    def save_photo(self, client_id, base64_data, photo_type="photo"):
        """Save a photo from webcam or file upload."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        subdir = "photos" if photo_type == "photo" else "ids"
        filename = f"{client_id}_{photo_type}_{timestamp}.png"
        filepath = os.path.join(MEDIA_DIR, subdir, filename)

        # Decode and save
        img_data = base64.b64decode(base64_data.split(",")[-1] if "," in base64_data else base64_data)
        with open(filepath, 'wb') as f:
            f.write(img_data)

        # Update client record
        conn = get_connection()
        c = conn.cursor()
        if photo_type == "photo":
            c.execute("UPDATE clients SET photo_path = ? WHERE id = ?", (filepath, client_id))
        elif photo_type == "id":
            c.execute("UPDATE clients SET id_photo_path = ? WHERE id = ?", (filepath, client_id))

        # Also save to documents table
        c.execute("""
            INSERT INTO documents (client_id, file_path, file_type, description, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (client_id, filepath, photo_type,
              f"{'Profile photo' if photo_type == 'photo' else 'ID Document'} captured",
              datetime.now().isoformat()))

        conn.commit()
        conn.close()
        return filepath

    def capture_photo_native(self, client_id, photo_type, title="Camera Capture"):
        """Use OpenCV native window to capture a photo securely and silently. 
        Spawns a new process to avoid macOS UI main thread crash from pywebview."""
        try:
            import multiprocessing
            import queue
            try:
                multiprocessing.set_start_method('spawn')
            except RuntimeError:
                pass # context already set
            
            q = multiprocessing.Queue()
            p = multiprocessing.Process(target=_camera_worker, args=(title, q))
            p.start()
            
            # Read from the queue before joining to prevent deadlocks (pipe buffer full).
            result = None
            while p.is_alive() or not q.empty():
                try:
                    result = q.get(timeout=0.1)
                    break
                except queue.Empty:
                    pass
            
            p.join(timeout=1.0)
            
            if result:
                if result.get("success"):
                    data_url = f"data:image/png;base64,{result['b64']}"
                    self.save_photo(client_id, data_url, photo_type)
                    return {"success": True, "message": "Photo captured and updated!"}
                else:
                    return {"success": False, "error": result.get("error")}
            else:
                return {"success": False, "error": "Camera process failed to return data."}

        except Exception as e:
            return {"success": False, "error": f"Camera spawn error: {e}"}

    def save_document(self, client_id, base64_data, filename, doc_type="other"):
        """Save an uploaded document."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        original_name = str(filename or "document").replace("\\", "/")
        safe_filename = os.path.basename(original_name).strip() or "document"
        safe_name = f"{client_id}_{timestamp}_{safe_filename}"
        filepath = os.path.join(MEDIA_DIR, "documents", safe_name)

        img_data = base64.b64decode(base64_data.split(",")[-1] if "," in base64_data else base64_data)
        with open(filepath, 'wb') as f:
            f.write(img_data)

        conn = get_connection()
        c = conn.cursor()
        c.execute("""
            INSERT INTO documents (client_id, file_path, file_type, description, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (client_id, filepath, doc_type, filename, datetime.now().isoformat()))
        conn.commit()
        conn.close()

        return filepath

    def delete_document(self, doc_id):
        """Delete a document by ID including the physical file on disk."""
        conn = None
        try:
            conn = get_connection()
            c = conn.cursor()
            c.execute("SELECT file_path FROM documents WHERE id = ?", (doc_id,))
            row = c.fetchone()
            
            if row:
                file_path = row[0]
                if os.path.exists(file_path):
                    os.remove(file_path)
                
                c.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
                conn.commit()
                return {"success": True}
            else:
                return {"success": False, "error": "Document not found."}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            if conn:
                conn.close()

    def rename_document(self, doc_id, new_name):
        """Rename the description/name of an existing document."""
        conn = None
        try:
            conn = get_connection()
            c = conn.cursor()
            c.execute("UPDATE documents SET description = ? WHERE id = ?", (new_name, doc_id))
            conn.commit()
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            if conn:
                conn.close()

    def save_signature(self, client_id, base64_data):
        """Save a digital signature/handwritten note."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{client_id}_signature_{timestamp}.png"
        filepath = os.path.join(MEDIA_DIR, "signatures", filename)

        img_data = base64.b64decode(base64_data.split(",")[-1] if "," in base64_data else base64_data)
        with open(filepath, 'wb') as f:
            f.write(img_data)

        conn = get_connection()
        c = conn.cursor()
        c.execute("""
            INSERT INTO documents (client_id, file_path, file_type, description, created_at)
            VALUES (?, ?, 'signature', 'Digital signature / handwritten note', ?)
        """, (client_id, filepath, datetime.now().isoformat()))
        conn.commit()
        conn.close()

        return filepath

    def get_client_documents(self, client_id):
        """Get all documents for a client."""
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM documents WHERE client_id = ? ORDER BY created_at DESC",
                  (client_id,))
        result = rows_to_list(c.fetchall())
        conn.close()
        return result

    def get_file_as_base64(self, filepath):
        """Read a file and return as base64 for display."""
        try:
            with open(filepath, 'rb') as f:
                data = f.read()
            ext = os.path.splitext(filepath)[1].lower()
            mime = {
                '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
                '.gif': 'image/gif', '.webp': 'image/webp', '.pdf': 'application/pdf'
            }.get(ext, 'application/octet-stream')
            return f"data:{mime};base64,{base64.b64encode(data).decode('utf-8')}"
        except Exception:
            return None

    # ═══════════════════════════════════════════════════════════════
    # PENALTIES
    # ═══════════════════════════════════════════════════════════════

    def apply_auto_penalties(self):
        """Create at most one automatic penalty per overdue installment."""
        conn = get_connection()
        try:
            c = conn.cursor()
            c.execute("""
                SELECT key, value FROM settings
                WHERE key IN ('auto_penalty_enabled', 'auto_penalty_rate',
                              'auto_penalty_grace_days', 'auto_penalty_type',
                              'auto_penalty_max_pct')
            """)
            settings = {row["key"]: row["value"] for row in c.fetchall()}
            if str(settings.get("auto_penalty_enabled", "false")).lower() != "true":
                return {"success": True, "created": 0, "enabled": False}
            rate = float(settings.get("auto_penalty_rate", 0) or 0)
            grace_days = max(0, int(settings.get("auto_penalty_grace_days", 3) or 0))
            penalty_type = str(settings.get("auto_penalty_type", "fixed") or "fixed").lower()
            max_pct = max(0.0, float(settings.get("auto_penalty_max_pct", 0) or 0))
            if rate <= 0 or penalty_type not in {"fixed", "percentage"}:
                return {"success": True, "created": 0, "enabled": True}

            today = datetime.now().date()
            cutoff = (today - relativedelta(days=grace_days)).strftime("%Y-%m-%d")
            c.execute("""
                SELECT a.id AS schedule_id, a.loan_id, l.client_id, l.principal,
                       a.due_date, a.total_due,
                       COALESCE(SUM(CASE WHEN p.voided_at IS NULL THEN pa.amount ELSE 0 END), 0) AS allocated
                FROM amortization_schedule a
                JOIN loans l ON l.id = a.loan_id
                LEFT JOIN payment_allocations pa ON pa.schedule_id = a.id
                LEFT JOIN payments p ON p.id = pa.payment_id
                LEFT JOIN penalties existing
                       ON existing.schedule_id = a.id AND existing.auto_generated = 1
                WHERE l.status IN ('active', 'defaulted')
                  AND a.due_date < ?
                  AND existing.id IS NULL
                GROUP BY a.id
                HAVING allocated < a.total_due - 0.005
                ORDER BY a.due_date
            """, (cutoff,))
            created = 0
            now = datetime.now().isoformat()
            for row in c.fetchall():
                outstanding = max(0.0, float(row["total_due"]) - float(row["allocated"]))
                amount = rate if penalty_type == "fixed" else outstanding * rate / 100
                amount = round(amount, 2)
                if max_pct > 0:
                    c.execute("""
                        SELECT COALESCE(SUM(amount), 0) FROM penalties
                        WHERE loan_id = ? AND auto_generated = 1 AND status != 'waived'
                    """, (row["loan_id"],))
                    already_penalized = float(c.fetchone()[0])
                    cap = float(row["principal"]) * max_pct / 100
                    amount = round(min(amount, max(0, cap - already_penalized)), 2)
                if amount <= 0:
                    continue
                days_overdue = max(0, (today - datetime.strptime(row["due_date"], "%Y-%m-%d").date()).days)
                c.execute("""
                    INSERT OR IGNORE INTO penalties
                        (loan_id, client_id, amount, reason, notes, status,
                         schedule_id, auto_generated, days_overdue_at_creation,
                         penalty_date, created_at)
                    VALUES (?, ?, ?, 'late_payment', ?, 'pending', ?, 1, ?, ?, ?)
                """, (
                    row["loan_id"], row["client_id"], amount,
                    f"Automatic late fee after {days_overdue} days overdue",
                    row["schedule_id"], days_overdue, today.isoformat(), now,
                ))
                if c.rowcount:
                    created += 1
                    self._audit_event(c, "auto_penalty_added", "schedule", row["schedule_id"], {
                        "loan_id": row["loan_id"], "amount": amount, "days_overdue": days_overdue,
                    })
            conn.commit()
            return {"success": True, "created": created, "enabled": True}
        except (TypeError, ValueError) as e:
            conn.rollback()
            app_logger.warning("Automatic penalties skipped: %s", e)
            return {"success": False, "error": str(e)}
        finally:
            conn.close()

    def add_penalty(self, loan_id, client_id, amount, reason, notes="", penalty_date=None):
        """Add a penalty (late payment, missed payment, etc.) to a loan."""
        conn = get_connection()
        try:
            c = conn.cursor()
            loan_id = int(loan_id)
            amount = float(amount)
            reason = str(reason or "").strip().lower()
            if not math.isfinite(amount) or amount <= 0:
                raise ValueError("Penalty amount must be greater than zero.")
            if reason not in {"late_payment", "missed_payment", "early_termination", "other"}:
                raise ValueError("Invalid penalty reason.")
            if not penalty_date:
                penalty_date = datetime.now().strftime("%Y-%m-%d")
            datetime.strptime(penalty_date, "%Y-%m-%d")
            c.execute(
                "SELECT id FROM loans WHERE id = ? AND client_id = ?",
                (loan_id, client_id)
            )
            if not c.fetchone():
                raise ValueError("Loan not found for this client.")
            now = datetime.now().isoformat()
            c.execute("""
                INSERT INTO penalties
                    (loan_id, client_id, amount, reason, notes, status, penalty_date, created_at)
                VALUES (?, ?, ?, ?, ?, 'pending', ?, ?)
            """, (loan_id, client_id, amount, reason, str(notes or "").strip(), penalty_date, now))
            penalty_id = c.lastrowid
            self._audit_event(c, "penalty_added", "penalty", penalty_id, {
                "loan_id": loan_id,
                "amount": amount,
                "reason": reason,
            })
            conn.commit()
            return penalty_id
        except (TypeError, ValueError) as e:
            conn.rollback()
            return {"success": False, "error": str(e)}
        finally:
            conn.close()

    def get_penalties(self, client_id=None, loan_id=None):
        """Get penalties, optionally filtered by client or loan."""
        conn = get_connection()
        c = conn.cursor()
        if loan_id:
            c.execute("""
                SELECT p.*, c.first_name, c.last_name
                FROM penalties p JOIN clients c ON p.client_id = c.id
                WHERE p.loan_id = ? ORDER BY p.penalty_date DESC
            """, (int(loan_id),))
        elif client_id:
            c.execute("""
                SELECT p.*, c.first_name, c.last_name
                FROM penalties p JOIN clients c ON p.client_id = c.id
                WHERE p.client_id = ? ORDER BY p.penalty_date DESC
            """, (client_id,))
        else:
            c.execute("""
                SELECT p.*, c.first_name, c.last_name
                FROM penalties p JOIN clients c ON p.client_id = c.id
                ORDER BY p.penalty_date DESC LIMIT 100
            """)
        result = rows_to_list(c.fetchall())
        conn.close()
        return result

    def update_penalty_status(self, penalty_id, status):
        """Update penalty status: pending → paid or waived."""
        status = str(status or "").strip().lower()
        if status not in {"pending", "paid", "waived"}:
            return {"success": False, "error": "Invalid penalty status."}
        conn = get_connection()
        c = conn.cursor()
        c.execute("UPDATE penalties SET status = ? WHERE id = ?", (status, int(penalty_id)))
        conn.commit()
        conn.close()
        return {"success": True, "status": status}

    # ═══════════════════════════════════════════════════════════════
    # LOAN ROLLOVER / REFINANCING HELPERS
    # ═══════════════════════════════════════════════════════════════

    def get_loan_rollover_info(self, loan_id):
        """
        Get remaining balance of a loan for rollover/renewal calculations.
        Returns dict with remaining, total_due, already_paid, months_paid,
        monthly_payment, and can_renew (True after 3 fully paid installments).
        """
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT principal, total_interest, total_repayment, monthly_payment, term_months FROM loans WHERE id = ?",
                  (int(loan_id),))
        loan = c.fetchone()
        if not loan:
            conn.close()
            return None
        total_due = _loan_repayment_total(loan)
        monthly_payment = loan['monthly_payment'] or 0

        c.execute("SELECT COALESCE(SUM(amount), 0) FROM payments WHERE loan_id = ? AND voided_at IS NULL",
                  (int(loan_id),))
        paid = c.fetchone()[0]

        months_paid = self._fully_paid_installment_count(c, int(loan_id))

        remaining = max(0, total_due - paid)
        conn.close()
        return {
            "loan_id": int(loan_id),
            "total_due": round(total_due, 2),
            "already_paid": round(paid, 2),
            "remaining": round(remaining, 2),
            "monthly_payment": round(monthly_payment, 2),
            "months_paid": months_paid,
            "can_renew": months_paid >= 3
        }

    def get_client_active_loan(self, client_id):
        """Return the active (or most recent non-paid) loan for a client, for rollover modal."""
        conn = get_connection()
        c = conn.cursor()
        c.execute("""
            SELECT l.id, l.principal, l.total_interest, l.total_repayment, l.status,
                   (SELECT COALESCE(SUM(amount), 0) FROM payments WHERE loan_id = l.id AND voided_at IS NULL) as total_paid
            FROM loans l WHERE l.client_id = ? AND l.status = 'active'
            ORDER BY l.created_at DESC LIMIT 1
        """, (client_id,))
        loan = dict_from_row(c.fetchone())
        conn.close()
        if loan:
            loan['remaining'] = round(_loan_repayment_total(loan) - loan['total_paid'], 2)
        return loan

    def calculate_dti(self, monthly_income, monthly_payment):
        """Calculate debt-to-income ratio as a percentage."""
        income = float(monthly_income or 0)
        payment = float(monthly_payment or 0)
        if not math.isfinite(income) or not math.isfinite(payment):
            return None
        if income <= 0 or payment < 0:
            return None
        dti = (payment / income) * 100
        return round(dti, 1)

    # ═══════════════════════════════════════════════════════════════
    # REFERRAL COMMISSIONS
    # ═══════════════════════════════════════════════════════════════

    def get_referral_commissions(self, client_id=None):
        """Get referral commissions, optionally filtered by referrer."""
        conn = get_connection()
        c = conn.cursor()

        if client_id:
            c.execute("""
                SELECT rc.*, 
                       r1.first_name as referrer_first, r1.last_name as referrer_last,
                       r2.first_name as referred_first, r2.last_name as referred_last
                FROM referral_commissions rc
                JOIN clients r1 ON rc.referrer_id = r1.id
                JOIN clients r2 ON rc.referred_id = r2.id
                WHERE rc.referrer_id = ? OR rc.referred_id = ?
                ORDER BY rc.created_at DESC
            """, (client_id, client_id))
        else:
            c.execute("""
                SELECT rc.*,
                       r1.first_name as referrer_first, r1.last_name as referrer_last,
                       r2.first_name as referred_first, r2.last_name as referred_last
                FROM referral_commissions rc
                JOIN clients r1 ON rc.referrer_id = r1.id
                JOIN clients r2 ON rc.referred_id = r2.id
                ORDER BY rc.created_at DESC
            """)
        result = rows_to_list(c.fetchall())
        conn.close()
        return result

    def mark_commission_paid(self, commission_id):
        """Mark a referral commission as paid."""
        conn = get_connection()
        c = conn.cursor()
        c.execute("UPDATE referral_commissions SET status = 'paid' WHERE id = ?",
                  (commission_id,))
        conn.commit()
        conn.close()
        return True

    # ═══════════════════════════════════════════════════════════════
    # EXPORT & REPORTS
    # ═══════════════════════════════════════════════════════════════

    def export_excel(self):
        """Export all data to Excel, save to exports dir, and auto-open."""
        try:
            export_dir = os.path.join(APP_SUPPORT_DIR, "exports")
            os.makedirs(export_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(export_dir, f"PH-Lending_Export_{timestamp}.xlsx")
            path = export_all_to_excel(output_path)
            _open_native(path)
            return {"success": True, "path": path}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def export_excel_selective(self, sheets, date_from=None, date_to=None):
        """
        Export selected data sheets to Excel.
        sheets: list of strings, e.g. ['clients', 'loans', 'payments']
        date_from / date_to: optional ISO date strings 'YYYY-MM-DD'
        """
        try:
            export_dir = os.path.join(APP_SUPPORT_DIR, "exports")
            os.makedirs(export_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            label = '_'.join(sorted(sheets)) if isinstance(sheets, list) and len(sheets) < 6 else 'all'
            output_path = os.path.join(export_dir, f"PH-Lending_{label}_{timestamp}.xlsx")
            path = export_selective(
                output_path,
                sheets if isinstance(sheets, list) else list(sheets),
                date_from or None,
                date_to or None
            )
            _open_native(path)
            return {"success": True, "path": path}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def generate_contract(self, loan_id):
        """Generate loan contract PDF and save to disk, then open."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"Contract_Loan_{loan_id}_{timestamp}.pdf"
            path = generate_contract_pdf(int(loan_id), output_path=os.path.join(PDF_DIR, filename))
            if path:
                _open_native(path)
                return {"success": True, "path": path, "filename": filename}
            return {"success": False, "error": "Loan not found"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def generate_receipt(self, payment_id):
        """Generate payment receipt PDF and save to disk, then open."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"Receipt_{payment_id}_{timestamp}.pdf"
            path = generate_receipt_pdf(int(payment_id), output_path=os.path.join(PDF_DIR, filename))
            if path:
                _open_native(path)
                return {"success": True, "path": path, "filename": filename}
            return {"success": False, "error": "Payment not found"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def print_multiple_pdfs(self, items):
        """
        Takes a list of items like:
        [{"type": "contract", "id": 1}, {"type": "receipt", "id": 5}, {"type": "document", "path": "..."}]
        Generates corresponding PDFs if needed and opens all of them at once in Preview for printing.
        """
        try:
            paths = []
            for item in items:
                t = item.get("type")
                if t == "contract":
                    filename = f"Contract_Loan_{item['id']}_Print.pdf"
                    out_path = os.path.join(PDF_DIR, filename)
                    generate_contract_pdf(int(item['id']), output_path=out_path)
                    if os.path.exists(out_path):
                        paths.append(out_path)
                elif t == "receipt":
                    filename = f"Receipt_{item['id']}_Print.pdf"
                    out_path = os.path.join(PDF_DIR, filename)
                    generate_receipt_pdf(int(item['id']), output_path=out_path)
                    if os.path.exists(out_path):
                        paths.append(out_path)
                elif t == "document":
                    p = item.get("path")
                    if p and os.path.exists(p) and p.lower().endswith(".pdf"):
                        paths.append(p)
            
            if not paths:
                return {"success": False, "error": "No valid PDFs generated or found."}
                
            # Open all together in Preview on macOS, or default PDF apps elsewhere.
            _open_native(paths, app='Preview' if sys.platform == "darwin" else None)
            return {"success": True, "count": len(paths)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def generate_amortization_pdf(self, loan_id):
        """
        Generate amortization schedule PDF, save it and return path + base64 for viewer.
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"Amortization_Loan_{loan_id}_{timestamp}.pdf"
            path = os.path.join(PDF_DIR, filename)
            result_path = generate_amortization_pdf(int(loan_id), output_path=path)
            if result_path:
                b64 = self._pdf_to_b64_datauri(result_path)
                return {"success": True, "path": result_path, "filename": filename, "b64": b64}
            return {"success": False, "error": "Loan not found"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def generate_contract_preview(self, loan_id):
        """
        Generate contract PDF and return path + base64 for inline viewer.
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"Contract_Loan_{loan_id}_{timestamp}.pdf"
            path = os.path.join(PDF_DIR, filename)
            result_path = generate_contract_pdf(int(loan_id), output_path=path)
            if result_path:
                b64 = self._pdf_to_b64_datauri(result_path)
                return {"success": True, "path": result_path, "filename": filename, "b64": b64}
            return {"success": False, "error": "Loan not found"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def generate_receipt_preview(self, payment_id):
        """
        Generate receipt PDF and return path + base64 for inline viewer.
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"Receipt_{payment_id}_{timestamp}.pdf"
            path = os.path.join(PDF_DIR, filename)
            result_path = generate_receipt_pdf(int(payment_id), output_path=path)
            if result_path:
                b64 = self._pdf_to_b64_datauri(result_path)
                return {"success": True, "path": result_path, "filename": filename, "b64": b64}
            return {"success": False, "error": "Payment not found"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def open_and_print_pdf(self, path):
        """Open a PDF in Preview for native printing."""
        try:
            if os.path.exists(path):
                _open_native(path, app='Preview' if sys.platform == "darwin" else None)
                return {"success": True}
            return {"success": False, "error": "File not found"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _pdf_to_b64_datauri(self, path):
        """Read a PDF file and return as data URI base64 string for iframe embedding."""
        try:
            with open(path, 'rb') as f:
                data = f.read()
            return "data:application/pdf;base64," + base64.b64encode(data).decode('utf-8')
        except Exception:
            return None

    # ═══════════════════════════════════════════════════════════════
    # BACKUP & SYNC
    # ═══════════════════════════════════════════════════════════════

    def do_backup_local(self):
        """Create local backup in 3 formats."""
        try:
            return backup_local()
        except Exception as e:
            return {"success": False, "errors": [str(e)]}

    def do_sync_drive(self):
        """Sync to Google Drive."""
        return sync_to_drive()

    def get_backup_info(self):
        """Get backup status and info."""
        return get_backup_status()

    def get_backups_list(self):
        """List all backups."""
        return list_backups()

    def restore_backup(self, backup_name):
        """Restore the active profile database from a named local backup."""
        if self._is_restricted_demo():
            return {"success": False, "error": "Backup restore is disabled in Demo Edition."}
        try:
            result = restore_local_backup(backup_name)
            init_database()
            app_logger.warning("Profile database restored from backup: %s", backup_name)
            return result
        except Exception as e:
            app_logger.log_exception("restore_backup", e)
            return {"success": False, "error": str(e)}

    def is_online(self):
        """Check internet connectivity."""
        return check_internet()

    def open_drive(self):
        """Open Google Drive folder in browser (or open credentials folder if not set up)."""
        url = open_drive_folder()
        if url:
            webbrowser.open(url)
            return {"success": True, "url": url}
        # Fall back to opening the data directory so user can drop credentials
        _open_native(APP_SUPPORT_DIR)
        return {"success": False, "opened_folder": True}

    def open_data_dir(self):
        """Open the application data directory."""
        _open_native(APP_SUPPORT_DIR)
        return True

    def open_excel_dir(self):
        """Open the exports directory."""
        export_dir = os.path.join(APP_SUPPORT_DIR, "exports")
        os.makedirs(export_dir, exist_ok=True)
        _open_native(export_dir)
        return True

    def open_pdf_dir(self):
        """Open the PDFs directory."""
        _open_native(PDF_DIR)
        return True

    def is_drive_setup(self):
        """Check if Google Drive is configured."""
        return is_drive_configured()

    # ═══════════════════════════════════════════════════════════════
    # SETTINGS
    # ═══════════════════════════════════════════════════════════════

    def get_settings(self):
        """Get all settings as a dict."""
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM settings")
        rows = c.fetchall()
        conn.close()
        return {r['key']: r['value'] for r in rows}

    def save_settings(self, data):
        """Save multiple settings."""
        try:
            normalized = dict(data or {})
            if "currency" in normalized:
                normalized["currency"] = normalize_currency(normalized["currency"])
            if "auto_penalty_type" in normalized and normalized["auto_penalty_type"] not in {"fixed", "percentage"}:
                raise ValueError("Invalid automatic penalty type.")
            for key in ("auto_penalty_rate", "auto_penalty_max_pct"):
                if key in normalized and float(normalized[key] or 0) < 0:
                    raise ValueError("Automatic penalty values cannot be negative.")
            if "auto_penalty_grace_days" in normalized:
                grace = int(normalized["auto_penalty_grace_days"] or 0)
                if grace < 0 or grace > 365:
                    raise ValueError("Grace period must be between 0 and 365 days.")
            conn = get_connection()
            try:
                c = conn.cursor()
                for key, value in normalized.items():
                    c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                              (key, str(value)))
                conn.commit()
            finally:
                conn.close()
            return True
        except (TypeError, ValueError) as e:
            return {"success": False, "error": str(e)}

    def save_logo(self, base64_data):
        """Save company logo image."""
        try:
            logo_path = os.path.join(APP_SUPPORT_DIR, "logo.png")
            img_data = base64.b64decode(base64_data.split(",")[-1] if "," in base64_data else base64_data)
            with open(logo_path, 'wb') as f:
                f.write(img_data)
            # Also save path in settings
            conn = get_connection()
            c = conn.cursor()
            c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('logo_path', ?)", (logo_path,))
            conn.commit()
            conn.close()
            return {"success": True, "path": logo_path}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_logo_base64(self):
        """Get company logo as base64 for display."""
        logo_path = os.path.join(APP_SUPPORT_DIR, "logo.png")
        if os.path.exists(logo_path):
            with open(logo_path, 'rb') as f:
                data = f.read()
            return "data:image/png;base64," + base64.b64encode(data).decode('utf-8')
        return None



    def get_app_info(self):
        """Get application info."""
        return {
            "version": "1.5.0",
            "name": APP_NAME,
            "demo_only": self._is_restricted_demo(),
            "demo_edition": self._demo_only,
            "data_dir": APP_SUPPORT_DIR,
            "db_path": get_db_path(),
            "media_dir": MEDIA_DIR,
            "pdf_dir": PDF_DIR
        }

    # ═══════════════════════════════════════════════════════════════
    # PROFILE MANAGEMENT
    # ═══════════════════════════════════════════════════════════════

    def get_profiles(self):
        """Get all profiles with sizes."""
        if self._is_restricted_demo():
            return []
        try:
            profiles = db_get_profiles()
            for p in profiles:
                db_path = os.path.join(APP_SUPPORT_DIR, p["db_file"])
                if os.path.exists(db_path):
                    size_bytes = os.path.getsize(db_path)
                    p["size"] = size_bytes
                    try:
                        import sqlite3 as _sq
                        _c = _sq.connect(db_path)
                        _c.row_factory = _sq.Row
                        p["client_count"] = _c.execute("SELECT COUNT(*) FROM clients").fetchone()[0]
                        p["loan_count"] = _c.execute("SELECT COUNT(*) FROM loans").fetchone()[0]
                        _c.close()
                    except Exception:
                        p["client_count"] = 0
                        p["loan_count"] = 0
                else:
                    p["size"] = 0
                    p["client_count"] = 0
                    p["loan_count"] = 0
            return profiles
        except Exception as e:
            app_logger.log_exception("get_profiles", e)
            return []

    def get_active_profile_info(self):
        """Get the currently active profile."""
        if self._is_restricted_demo():
            return {"id": "demo", "name": "Demo Edition", "is_active": True}
        try:
            return db_get_active_profile()
        except Exception as e:
            app_logger.log_exception("get_active_profile_info", e)
            return {"id": "default", "name": "Main Profile", "is_active": True}

    def create_new_profile(self, name, description="", color="#007AFF"):
        """Create a new profile."""
        if self._is_restricted_demo():
            return {"success": False, "error": "Profiles are disabled in Demo Edition."}
        try:
            if not name or not name.strip():
                return {"success": False, "error": "Profile name is required."}
            profile = db_create_profile(name.strip(), description.strip(), color)
            app_logger.info("Profile created: %s (%s)", profile["name"], profile["id"])
            return {"success": True, "profile": profile}
        except Exception as e:
            app_logger.log_exception("create_new_profile", e)
            return {"success": False, "error": str(e)}

    def switch_active_profile(self, profile_id):
        """Switch to a different profile. Re-initializes the database connection."""
        if self._is_restricted_demo():
            return {"success": False, "error": "Profiles are disabled in Demo Edition."}
        try:
            result = db_switch_profile(profile_id)
            if result:
                init_database()
                self._reset_startup_auth_session()
                app_logger.info("Switched to profile: %s", profile_id)
                return {
                    "success": True,
                    "auth_required": self._startup_login_required,
                }
            return {"success": False, "error": "Profile not found."}
        except Exception as e:
            app_logger.log_exception("switch_active_profile", e)
            return {"success": False, "error": str(e)}

    def rename_existing_profile(self, profile_id, new_name, new_description=None, new_color=None):
        """Rename a profile."""
        if self._is_restricted_demo():
            return {"success": False, "error": "Profiles are disabled in Demo Edition."}
        try:
            result = db_rename_profile(profile_id, new_name, new_description, new_color)
            if result:
                return {"success": True}
            return {"success": False, "error": "Profile not found."}
        except Exception as e:
            app_logger.log_exception("rename_existing_profile", e)
            return {"success": False, "error": str(e)}

    def delete_existing_profile(self, profile_id):
        """Delete a profile (cannot delete 'default')."""
        if self._is_restricted_demo():
            return {"success": False, "error": "Profiles are disabled in Demo Edition."}
        try:
            result = db_delete_profile(profile_id)
            if result:
                init_database()
                app_logger.info("Profile deleted: %s", profile_id)
                return {"success": True}
            return {"success": False, "error": "Cannot delete the default profile."}
        except Exception as e:
            app_logger.log_exception("delete_existing_profile", e)
            return {"success": False, "error": str(e)}

    def reset_current_profile(self):
        """Wipe ALL data in the current profile. Settings stay. Backup is forced first."""
        if self._is_restricted_demo():
            return {"success": False, "error": "Use Regenerate Demo Data in Demo Edition."}
        try:
            try:
                from backup import backup_local
                backup_local()
            except Exception as be:
                app_logger.log_exception("reset_current_profile > backup", be)

            reset_profile_data()
            app_logger.info("Profile data reset for profile: %s",
                          db_get_active_profile().get("name", "unknown"))
            return {"success": True, "message": "All data has been erased. Settings preserved."}
        except Exception as e:
            app_logger.log_exception("reset_current_profile", e)
            return {"success": False, "error": str(e)}

    # ═══════════════════════════════════════════════════════════════
    # PASSWORD PROTECTION
    # ═══════════════════════════════════════════════════════════════

    def get_startup_auth_state(self):
        """Return only the non-sensitive state needed by the opening screen."""
        try:
            now = time.monotonic()
            if self._login_blocked_until and now >= self._login_blocked_until:
                self._login_blocked_until = 0.0
                self._login_failures = 0
            security = self._read_startup_security()
            profile = db_get_active_profile() or {}
            login_enabled = bool(security["login_enabled"])
            self._startup_login_required = login_enabled
            if not login_enabled:
                self._session_authenticated = True
            return {
                "success": True,
                "required": login_enabled,
                "login_enabled": login_enabled,
                "authenticated": bool(self._session_authenticated),
                "password_configured": bool(security["password_ready"]),
                "profile_name": profile.get("name", "Main Profile"),
                "company_name": security["company_name"],
                "retry_after": max(0, int(math.ceil(self._login_blocked_until - now))),
            }
        except Exception as e:
            app_logger.log_exception("get_startup_auth_state", e)
            return {
                "success": False,
                "required": False,
                "authenticated": True,
                "error": "Could not read the startup security settings.",
            }

    def authenticate_startup(self, password):
        """Unlock the active profile for this application session."""
        try:
            security = self._read_startup_security()
            if not security["login_enabled"]:
                self._startup_login_required = False
                self._session_authenticated = True
                return {"success": True, "authenticated": True}

            now = time.monotonic()
            retry_after = int(math.ceil(self._login_blocked_until - now))
            if retry_after > 0:
                return {
                    "success": False,
                    "authenticated": False,
                    "retry_after": retry_after,
                    "error": f"Too many attempts. Try again in {retry_after} seconds.",
                }

            valid, needs_upgrade = _verify_profile_password(
                password,
                security["password_hash"],
            )
            if valid:
                if needs_upgrade:
                    conn = get_connection()
                    try:
                        conn.execute(
                            "INSERT OR REPLACE INTO settings (key, value) VALUES ('profile_password', ?)",
                            (_hash_profile_password(password),),
                        )
                        conn.commit()
                    finally:
                        conn.close()
                self._session_authenticated = True
                self._login_failures = 0
                self._login_blocked_until = 0.0
                app_logger.info("Startup profile unlocked successfully.")
                return {"success": True, "authenticated": True}

            self._login_failures += 1
            attempts_remaining = max(0, 5 - self._login_failures)
            response = {
                "success": False,
                "authenticated": False,
                "attempts_remaining": attempts_remaining,
                "error": "Incorrect password.",
            }
            if self._login_failures >= 5:
                self._login_failures = 0
                self._login_blocked_until = now + 30
                response.update({
                    "retry_after": 30,
                    "error": "Too many attempts. Try again in 30 seconds.",
                })
            app_logger.warning("Failed startup unlock attempt.")
            return response
        except Exception as e:
            app_logger.log_exception("authenticate_startup", e)
            return {
                "success": False,
                "authenticated": False,
                "error": "Could not verify the password.",
            }

    def lock_session(self):
        """Return to the opening screen without closing the application."""
        security = self._read_startup_security()
        if not security["login_enabled"]:
            return {"success": False, "error": "Startup login is not enabled."}
        self._startup_login_required = True
        self._session_authenticated = False
        self._login_failures = 0
        self._login_blocked_until = 0.0
        app_logger.info("Application session locked.")
        return {"success": True, "locked": True}

    def set_profile_password(self, password, enable_startup_login=None):
        """Set the profile password and optionally enable startup login."""
        try:
            password = str(password or "")
            if len(password) < 8:
                raise ValueError("Password must be at least 8 characters.")
            encoded_hash = _hash_profile_password(password)
            conn = get_connection()
            c = conn.cursor()
            c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('profile_password', ?)", (encoded_hash,))
            c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('password_enabled', 'true')")
            if enable_startup_login is not None:
                c.execute(
                    "INSERT OR REPLACE INTO settings (key, value) VALUES ('startup_login_enabled', ?)",
                    ('true' if bool(enable_startup_login) else 'false',),
                )
            conn.commit()
            conn.close()
            security = self._read_startup_security()
            self._startup_login_required = bool(security["login_enabled"])
            self._session_authenticated = True
            app_logger.info("Profile password has been set.")
            return {
                "success": True,
                "startup_login_enabled": self._startup_login_required,
            }
        except Exception as e:
            app_logger.log_exception("set_profile_password", e)
            return {"success": False, "error": str(e)}

    def verify_profile_password(self, password):
        """Verify a password against the stored hash."""
        try:
            conn = get_connection()
            c = conn.cursor()
            c.execute("SELECT value FROM settings WHERE key = 'profile_password'")
            row = c.fetchone()
            stored_hash = row[0] if row else ""
            valid, needs_upgrade = _verify_profile_password(password, stored_hash)
            if valid and needs_upgrade:
                c.execute(
                    "INSERT OR REPLACE INTO settings (key, value) VALUES ('profile_password', ?)",
                    (_hash_profile_password(password),)
                )
                conn.commit()
                app_logger.info("Legacy profile password hash upgraded.")
            conn.close()
            if valid:
                return {"success": True, "valid": True}
            return {"success": True, "valid": False}
        except Exception as e:
            app_logger.log_exception("verify_profile_password", e)
            return {"success": False, "error": str(e)}

    def remove_profile_password(self):
        """Remove the password protection."""
        try:
            conn = get_connection()
            c = conn.cursor()
            c.execute("DELETE FROM settings WHERE key = 'profile_password'")
            c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('password_enabled', 'false')")
            c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('startup_login_enabled', 'false')")
            conn.commit()
            conn.close()
            self._startup_login_required = False
            self._session_authenticated = True
            app_logger.info("Profile password has been removed.")
            return {"success": True}
        except Exception as e:
            app_logger.log_exception("remove_profile_password", e)
            return {"success": False, "error": str(e)}

    def is_password_protected(self):
        """Check if password protection is enabled."""
        try:
            conn = get_connection()
            c = conn.cursor()
            c.execute("SELECT value FROM settings WHERE key = 'password_enabled'")
            row = c.fetchone()
            conn.close()
            return row is not None and row[0] == 'true'
        except Exception:
            return False

    def set_startup_login_enabled(self, enabled):
        """Enable or disable the opening login screen for the active profile."""
        try:
            enabled = bool(enabled)
            security = self._read_startup_security()
            if enabled and not security["password_ready"]:
                return {
                    "success": False,
                    "error": "Set a profile password before enabling startup login.",
                }
            conn = get_connection()
            try:
                conn.execute(
                    "INSERT OR REPLACE INTO settings (key, value) VALUES ('startup_login_enabled', ?)",
                    ('true' if enabled else 'false',),
                )
                conn.commit()
            finally:
                conn.close()
            self._startup_login_required = enabled
            # Changing the preference never locks the current working session.
            self._session_authenticated = True
            app_logger.info("Startup login set to: %s", enabled)
            return {"success": True, "enabled": enabled}
        except Exception as e:
            app_logger.log_exception("set_startup_login_enabled", e)
            return {"success": False, "error": str(e)}

    # ═══════════════════════════════════════════════════════════════
    # APP LIFECYCLE
    # ═══════════════════════════════════════════════════════════════


    # ═══════════════════════════════════════════════════════════════
    # OVERDUE ALERTS & SMS
    # ═══════════════════════════════════════════════════════════════

    def get_overdue_alerts(self):
        """
        Return active loans with installments that are past due and not fully paid.

        Payment allocations are the source of truth. Dividing total payments by
        a nominal monthly installment is incorrect for declining schedules,
        partial payments, and loans whose remaining term was extended.
        """
        self.apply_auto_penalties()
        conn = get_connection()
        try:
            c = conn.cursor()
            today = datetime.now().strftime("%Y-%m-%d")
            c.execute("""
                SELECT
                    c.id AS client_id,
                    c.first_name,
                    c.last_name,
                    c.contact,
                    c.rating,
                    l.id AS loan_id,
                    l.principal,
                    l.monthly_payment,
                    a.id AS schedule_id,
                    a.due_date,
                    a.total_due,
                    COALESCE(SUM(
                        CASE WHEN p.voided_at IS NULL THEN pa.amount ELSE 0 END
                    ), 0) AS allocated
                FROM amortization_schedule a
                JOIN loans l ON l.id = a.loan_id
                JOIN clients c ON c.id = l.client_id
                LEFT JOIN payment_allocations pa ON pa.schedule_id = a.id
                LEFT JOIN payments p ON p.id = pa.payment_id
                WHERE a.due_date <= ?
                  AND l.status = 'active'
                GROUP BY a.id
                HAVING allocated < a.total_due - 0.005
                ORDER BY l.id, a.due_date
            """, (today,))

            grouped = {}
            for row in rows_to_list(c.fetchall()):
                alert = grouped.setdefault(row["loan_id"], {
                    "client_id": row["client_id"],
                    "first_name": row["first_name"],
                    "last_name": row["last_name"],
                    "contact": row["contact"] or "",
                    "rating": row["rating"],
                    "loan_id": row["loan_id"],
                    "principal": round(row["principal"], 2),
                    "monthly_payment": round(row["monthly_payment"], 2),
                    "missed_count": 0,
                    "total_overdue_amount": 0.0,
                    "earliest_due": row["due_date"],
                })
                alert["missed_count"] += 1
                alert["total_overdue_amount"] += max(
                    0.0, float(row["total_due"]) - float(row["allocated"])
                )

            now = datetime.now()
            alerts = []
            for alert in grouped.values():
                first_unpaid = datetime.strptime(alert["earliest_due"], "%Y-%m-%d")
                days_overdue = max(0, (now - first_unpaid).days)
                if days_overdue >= 60:
                    severity = "critical"
                elif days_overdue >= 30:
                    severity = "high"
                elif days_overdue >= 14:
                    severity = "medium"
                else:
                    severity = "low"

                alert["total_overdue_amount"] = round(
                    alert["total_overdue_amount"], 2
                )
                alert["days_overdue"] = days_overdue
                alert["severity"] = severity
                alerts.append(alert)

            alerts.sort(key=lambda item: item["days_overdue"], reverse=True)
            return alerts
        finally:
            conn.close()

    def get_overdue_count(self):
        """Quick count of overdue loans for the sidebar badge."""
        alerts = self.get_overdue_alerts()
        return len(alerts)

    def send_sms_via_phone(self, phone_number, message):
        """
        Send SMS using the iPhone connected to Mac via Continuity (Handoff/SMS relay).
        Uses AppleScript to open a NEW, separate Messages.app conversation window for
        each recipient — avoiding the sms:// protocol which always overwrites the same
        draft window and loses previously queued messages in bulk sends.
        Requires iPhone and Mac signed into the same Apple ID with SMS relay enabled.
        """
        try:
            # Format phone number — remove spaces/dashes, ensure it's clean
            clean_phone = ''.join(filter(lambda x: x.isdigit() or x == '+', phone_number))
            if not clean_phone:
                return {"success": False, "error": "Invalid phone number"}

            # Escape double-quotes and backslashes in the message for AppleScript
            safe_message = message.replace('\\', '\\\\').replace('"', '\\"')

            # AppleScript: creates a new chat with the recipient and pre-fills the message.
            # Each call opens its own independent conversation — bulk sends are preserved.
            apple_script = f'''
tell application "Messages"
    activate
    set targetService to 1st service whose service type = SMS
    set targetBuddy to buddy "{clean_phone}" of targetService
    set newChat to make new text chat with properties {{participants: {{targetBuddy}}}}
    send "{safe_message}" to newChat
end tell
'''
            result = subprocess.run(
                ['osascript', '-e', apple_script],
                capture_output=True, text=True, timeout=10
            )

            if result.returncode != 0:
                # AppleScript failed — fall back to sms:// URI as last resort
                import urllib.parse
                encoded_msg = urllib.parse.quote(message)
                sms_url = f"sms:{clean_phone}&body={encoded_msg}"
                _open_native(sms_url)
                return {
                    "success": True,
                    "method": "phone_fallback",
                    "phone": clean_phone,
                    "warning": "AppleScript failed, opened via sms:// (last recipient only visible)"
                }

            return {"success": True, "method": "phone", "phone": clean_phone}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def send_sms_via_api(self, phone_number, message):
        """
        Send SMS via API (supports Twilio and Semaphore Philippines).
        Reads API config from settings: sms_provider, sms_api_key, sms_sender_id.
        """
        try:
            conn = get_connection()
            c = conn.cursor()
            c.execute("SELECT key, value FROM settings WHERE key LIKE 'sms_%'")
            sms_settings = {r['key']: r['value'] for r in c.fetchall()}
            conn.close()

            provider    = sms_settings.get('sms_provider', 'semaphore')
            api_key     = sms_settings.get('sms_api_key', '')
            sender_id   = sms_settings.get('sms_sender_id', 'LENDING')

            if not api_key:
                return {"success": False, "error": "API key not configured. Please set it in Settings > SMS."}

            # Preserve the caller's international country code.
            clean_phone = ''.join(filter(lambda x: x.isdigit() or x == '+', phone_number))
            if not re.fullmatch(r"\+[1-9]\d{7,14}", clean_phone):
                return {
                    "success": False,
                    "error": "Use an international phone number such as +41791234567.",
                }

            import urllib.request
            import urllib.parse

            if provider == 'semaphore':
                # Semaphore Philippines API
                payload = urllib.parse.urlencode({
                    'apikey': api_key,
                    'number': clean_phone,
                    'message': message,
                    'sendername': sender_id
                }).encode('utf-8')
                req = urllib.request.Request(
                    'https://api.semaphore.co/api/v4/messages',
                    data=payload,
                    method='POST'
                )
                with urllib.request.urlopen(req, timeout=15) as resp:
                    result = json.loads(resp.read().decode())
                return {"success": True, "method": "api", "provider": "semaphore", "result": result}

            elif provider == 'twilio':
                # Twilio REST API
                account_sid = sms_settings.get('sms_account_sid', '')
                if not account_sid:
                    return {"success": False, "error": "Twilio Account SID manquant"}
                from_number = sms_settings.get('sms_from_number', '')

                credentials = base64.b64encode(f"{account_sid}:{api_key}".encode()).decode()
                payload = urllib.parse.urlencode({
                    'To':   clean_phone,
                    'From': from_number,
                    'Body': message
                }).encode('utf-8')
                req = urllib.request.Request(
                    f'https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json',
                    data=payload,
                    headers={'Authorization': f'Basic {credentials}'},
                    method='POST'
                )
                with urllib.request.urlopen(req, timeout=15) as resp:
                    result = json.loads(resp.read().decode())
                return {"success": True, "method": "api", "provider": "twilio", "result": result}

            else:
                return {"success": False, "error": f"Provider SMS inconnu: {provider}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_sms_templates(self):
        """Return saved SMS templates from settings."""
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT value FROM settings WHERE key = 'sms_templates'")
        row = c.fetchone()
        conn.close()

        default_templates = [
            {
                "id": "reminder",
                "name": "Payment Reminder",
                "text": "Hi {name}, your payment of {amount} was due on {date}. Please settle your balance as soon as possible. — {company}"
            },
            {
                "id": "overdue",
                "name": "Urgent Overdue",
                "text": "URGENT: {name}, your payment of {amount} is {days} days overdue. Please contact us immediately at {phone}. — {company}"
            },
            {
                "id": "final",
                "name": "Final Warning",
                "text": "FINAL WARNING — {name}: A balance of {amount} has been overdue for {days} days. Failure to pay within 48 hours may result in legal action. — {company}"
            }
        ]

        if row and row['value']:
            try:
                return json.loads(row['value'])
            except Exception:
                return default_templates
        return default_templates

    def save_sms_templates(self, templates):
        """Save SMS templates to settings."""
        conn = get_connection()
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('sms_templates', ?)",
                  (json.dumps(templates),))
        conn.commit()
        conn.close()
        return True

    def shutdown_services(self, force_backup=True):
        """Stop backups and the local HTTP server exactly once."""
        with self._shutdown_lock:
            if self._shutdown_started:
                return {"backup": None, "already_stopped": True}
            self._shutdown_started = True

        result = {"backup": None, "services_stopped": True}
        if force_backup:
            try:
                result["backup"] = backup_local()
            except Exception as e:
                result["backup_error"] = str(e)

        server = self._server
        self._server = None
        if server is not None:
            try:
                server.shutdown()
                server.server_close()
            except Exception as e:
                result["server_error"] = str(e)
        return result

    def quit_app(self, force_backup=True):
        """
        Gracefully quit the application:
        1. Perform a backup (if not done recently and force_backup=True)
        2. Close the pywebview window
        3. Exit the Python process
        """
        result = self.shutdown_services(force_backup=force_backup)
        result["quitting"] = True

        # Destroy the window (triggers pywebview shutdown loop to exit)
        try:
            if hasattr(self, '_window') and self._window:
                self._window.destroy()
        except Exception:
            pass

        # Final fallback if the native webview does not return after destroy.
        def _exit():
            import time
            time.sleep(2.0)
            import os as _os
            _os._exit(0)
        threading.Thread(target=_exit, daemon=True).start()

        return result

    # ═══════════════════════════════════════════════════════════════
    # SYSTEM LOGS
    # ═══════════════════════════════════════════════════════════════

    def get_logs(self, limit=200, level_filter="ALL"):
        """Return recent log entries for display in the frontend."""
        try:
            return {
                "success": True,
                "entries": app_logger.get_log_entries(int(limit), level_filter)
            }
        except Exception as e:
            app_logger.log_exception("get_logs", e)
            return {"success": False, "entries": [], "error": str(e)}

    def get_log_stats(self):
        """Return stats about the log file (size, error count, etc.)."""
        try:
            return app_logger.get_log_stats()
        except Exception as e:
            app_logger.log_exception("get_log_stats", e)
            return {"exists": False, "error": str(e)}

    def get_audit_events(self, limit=100):
        """Return recent business audit events."""
        conn = get_connection()
        try:
            c = conn.cursor()
            c.execute("""
                SELECT *
                FROM audit_events
                ORDER BY created_at DESC, id DESC
                LIMIT ?
            """, (int(limit),))
            events = rows_to_list(c.fetchall())
            for event in events:
                try:
                    event["details"] = json.loads(event.get("details") or "{}")
                except Exception:
                    event["details"] = {}
            return events
        finally:
            conn.close()

    def clear_logs(self):
        """Clear the current log file."""
        try:
            ok = app_logger.clear_logs()
            return {"success": ok}
        except Exception as e:
            app_logger.log_exception("clear_logs", e)
            return {"success": False, "error": str(e)}

    def log_frontend_error(self, context, message, stack=""):
        """
        Called by the JavaScript frontend to log client-side errors.
        This lets us capture JS crashes in the same persistent log file.
        """
        try:
            full_msg = f"[JS/{context}] {message}"
            if stack:
                full_msg += f"\n{stack}"
            app_logger.error(full_msg)
            return {"success": True}
        except Exception:
            return {"success": False}
