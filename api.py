"""
PH-Lending Pro — Main API
Exposed to the frontend via pywebview's js_api bridge.
All methods are callable from JavaScript as pywebview.api.<method_name>()
"""

import os
import sys
import json
import sqlite3
import base64
import subprocess
import webbrowser
import traceback
from datetime import datetime

import logger as app_logger  # persistent error logger

from database import (
    get_connection, dict_from_row, rows_to_list,
    init_database, generate_client_id, MEDIA_DIR, APP_SUPPORT_DIR,
    set_demo_mode, load_active_profile,
    get_profiles as db_get_profiles, get_active_profile as db_get_active_profile,
    create_profile as db_create_profile, switch_profile as db_switch_profile,
    rename_profile as db_rename_profile, delete_profile as db_delete_profile,
    reset_profile_data, get_db_path
)
from loan_engine import generate_amortization_schedule, get_loan_summary
from pdf_generator import generate_contract_pdf, generate_receipt_pdf, generate_amortization_pdf
from excel_export import export_all_to_excel, export_selective
from backup import (
    backup_local, get_backup_status, list_backups,
    sync_to_drive, open_drive_folder, is_drive_configured, check_internet
)

PDF_DIR = os.path.join(APP_SUPPORT_DIR, "pdfs")
os.makedirs(PDF_DIR, exist_ok=True)

VALID_PAYMENT_METHODS = {"cash", "gcash", "bank_transfer", "check"}
PAYMENT_METHOD_ALIASES = {
    "bank": "bank_transfer",
    "bank transfer": "bank_transfer",
    "bank-transfer": "bank_transfer",
}


def _normalize_payment_method(method):
    normalized = str(method or "cash").strip().lower()
    normalized = PAYMENT_METHOD_ALIASES.get(normalized, normalized)
    if normalized not in VALID_PAYMENT_METHODS:
        raise ValueError(
            "Invalid payment method. Use cash, gcash, bank_transfer, or check."
        )
    return normalized


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
            cv2.putText(display_frame, "ESPACE=Prendre, ECHAP=Annuler", (20, 40), 
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

    def __init__(self):
        load_active_profile()  # Restore active profile from saved metadata
        init_database()
        self._is_demo = False

    def toggle_demo_mode(self, enabled):
        """Toggle demo mode (uses a separate prepopulated database)."""
        self._is_demo = enabled
        set_demo_mode(enabled)
        # Verify if demo DB is empty and auto-generate if needed
        if enabled:
            conn = get_connection()
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM clients")
            count = c.fetchone()[0]
            conn.close()
            if count == 0:
                try:
                    import demo_generator
                    demo_generator.generate_demo_data()
                except Exception as e:
                    app_logger.log_exception("toggle_demo_mode > generate_demo_data", e)
                    print(f"Error generating demo data: {e}")
        app_logger.info("Demo mode set to: %s", enabled)
        return {"success": True, "demo_active": enabled}

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
            for table in ['referral_commissions', 'penalties', 'payments',
                          'amortization_schedule', 'loans', 'documents', 'clients']:
                c.execute(f"DELETE FROM {table}")
            # Reset auto-increment sequences
            c.execute("DELETE FROM sqlite_sequence WHERE name IN ('loans','payments','amortization_schedule','penalties','documents','referral_commissions')")
            conn.commit()
            conn.close()

            # Re-generate fresh scenarios
            import importlib, demo_generator
            importlib.reload(demo_generator)
            demo_generator.generate_demo_data()

            return {"success": True, "message": "Données de démo régénérées avec succès !"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_demo_status(self):
        """Check if demo mode is active."""
        return self._is_demo

    def open_file(self, file_path):
        """Open any existing file or directory natively."""
        if file_path and os.path.exists(file_path):
            return _open_native(file_path)
        return False

    def open_url(self, url):
        """Open a URL in the system default browser (used for social media links)."""
        try:
            if not url or not (url.startswith('http://') or url.startswith('https://')):
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

        # Total interest earned (from payments on active+paid loans)
        c.execute("""
            SELECT COALESCE(SUM(p.amount), 0)
            FROM payments p
            JOIN loans l ON p.loan_id = l.id
        """)
        total_collected = c.fetchone()[0]

        # Total expected interest
        c.execute("SELECT COALESCE(SUM(total_interest), 0) FROM loans")
        total_expected_interest = c.fetchone()[0]

        # Interest collected (total collected - total principal paid back)
        c.execute("SELECT COALESCE(SUM(principal), 0) FROM loans WHERE status = 'paid'")
        principal_paid_back = c.fetchone()[0]
        interest_collected = max(0, total_collected - principal_paid_back)

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

        # Today's unpaid collections only. Paid installments must not remain due.
        today = datetime.now().strftime("%Y-%m-%d")
        today_rows = self.get_collections_by_date(today)
        today_collections = len(today_rows)
        today_amount = sum(row.get("total_due", 0) for row in today_rows)

        return {
            "active_capital": round(active_capital, 2),
            "total_capital": round(total_capital, 2),
            "interest_collected": round(interest_collected, 2),
            "total_expected_interest": round(total_expected_interest, 2),
            "total_collected": round(total_collected, 2),
            "client_count": client_count,
            "active_loans": active_loans,
            "defaulted_loans": defaulted_loans,
            "delinquency_rate": delinquency_rate,
            "today_collections": today_collections,
            "today_amount": round(today_amount, 2)
        }

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
                ORDER BY {sort} {order}
                LIMIT ? OFFSET ?
            """, (search_param, search_param, search_param, search_param, per_page, offset))
            rows = rows_to_list(c.fetchall())

            c.execute("""
                SELECT COUNT(*) FROM clients
                WHERE first_name LIKE ? OR last_name LIKE ? OR id LIKE ? OR contact LIKE ?
            """, (search_param, search_param, search_param, search_param))
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
                   (SELECT COALESCE(SUM(amount), 0) FROM payments WHERE loan_id = l.id) as total_paid
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

        conn.close()
        return client

    def create_client(self, data):
        """Create a new client. Returns the new client ID."""
        conn = get_connection()
        c = conn.cursor()
        now = datetime.now().isoformat()
        client_id = generate_client_id()

        c.execute("""
            INSERT INTO clients (id, first_name, last_name, address, address_detail, contact, email,
                                 rating, referred_by, notes, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            client_id,
            data.get('first_name', ''),
            data.get('last_name', ''),
            data.get('address', ''),
            data.get('address_detail', ''),
            data.get('contact', ''),
            data.get('email', ''),
            data.get('rating', 3),
            data.get('referred_by') or None,
            data.get('notes', ''),
            now, now
        ))
        conn.commit()
        conn.close()
        return client_id

    def update_client(self, client_id, data):
        """Update client details."""
        conn = get_connection()
        c = conn.cursor()
        now = datetime.now().isoformat()

        fields = []
        values = []
        for key in ['first_name', 'last_name', 'address', 'address_detail', 'contact', 'email',
                     'rating', 'referred_by', 'notes', 'photo_path',
                     'id_photo_path', 'monthly_income', 'social_media']:
            if key in data:
                fields.append(f"{key} = ?")
                values.append(data[key] if data[key] != '' else (None if key == 'referred_by' else ''))

        fields.append("updated_at = ?")
        values.append(now)
        values.append(client_id)

        c.execute(f"UPDATE clients SET {', '.join(fields)} WHERE id = ?", values)
        conn.commit()
        conn.close()
        return True

    def delete_client(self, client_id):
        """Delete a client and all related data."""
        conn = get_connection()
        c = conn.cursor()
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

    def calculate_loan_preview(self, principal, rate, interest_type, term_months):
        """Preview loan calculations without creating."""
        return get_loan_summary(float(principal), float(rate), interest_type, int(term_months))

    def create_loan(self, client_id, principal, rate, interest_type, term_months, start_date,
                    rollover_from_loan_id=None, renewal_mode=False):
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
            if new_principal <= 0:
                raise ValueError("Principal must be greater than zero.")
            if rate <= 0:
                raise ValueError("Interest rate must be greater than zero.")
            if term_months < 1:
                raise ValueError("Loan term must be at least 1 month.")
            if interest_type not in {"fixed", "declining"}:
                raise ValueError("Interest type must be fixed or declining.")
            datetime.strptime(start_date, "%Y-%m-%d")

            rollover_amount = 0.0
            cash_given_to_client = new_principal  # default: full principal is cash
            rollover_id = int(rollover_from_loan_id) if rollover_from_loan_id else None

            # Handle rollover / refinancing
            if rollover_id:
                c.execute(
                    "SELECT principal, total_interest, status FROM loans WHERE id = ? AND client_id = ?",
                    (rollover_id, client_id)
                )
                old_loan = c.fetchone()
                if not old_loan:
                    raise ValueError("Original loan not found for this client.")
                if old_loan["status"] != "active":
                    raise ValueError("Only active loans can be refinanced.")

                c.execute("SELECT COUNT(*) FROM payments WHERE loan_id = ?", (rollover_id,))
                paid_count = c.fetchone()[0]
                if renewal_mode and paid_count < 3:
                    raise ValueError("Renewal requires at least 3 recorded payments on the active loan.")

                total_due_old = old_loan['principal'] + old_loan['total_interest']
                c.execute("SELECT COALESCE(SUM(amount), 0) FROM payments WHERE loan_id = ?",
                          (rollover_id,))
                already_paid = c.fetchone()[0]
                rollover_amount = max(0, total_due_old - already_paid)

                if renewal_mode:
                    # RENEWAL MODE: total new credit = principal, client receives the difference.
                    cash_given_to_client = max(0, new_principal - rollover_amount)
                else:
                    # CLASSIC ROLLOVER: add remaining balance on top of new capital.
                    new_principal += rollover_amount
                    cash_given_to_client = new_principal - rollover_amount

                c.execute("UPDATE loans SET status = 'refinanced' WHERE id = ?", (rollover_id,))

            # Calculate loan
            summary = get_loan_summary(new_principal, rate, interest_type, term_months)
            schedule = generate_amortization_schedule(
                new_principal, rate, interest_type, term_months, start_date
            )
            if not schedule:
                raise ValueError("Could not generate amortization schedule.")

            # Insert loan
            c.execute("""
                INSERT INTO loans (client_id, principal, interest_rate, interest_type,
                                  term_months, start_date, status, total_interest,
                                  monthly_payment, original_loan_id, rollover_amount, created_at)
                VALUES (?, ?, ?, ?, ?, ?, 'active', ?, ?, ?, ?, ?)
            """, (
                client_id, new_principal, rate, interest_type, term_months,
                start_date, summary['total_interest'], summary['monthly_payment'],
                rollover_id, rollover_amount, now
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

            conn.commit()
            app_logger.info("Loan created: loan_id=%s client_id=%s principal=%.2f renewal_mode=%s",
                            loan_id, client_id, new_principal, renewal_mode)
            return {
                "success": True,
                "loan_id": loan_id,
                "rollover_amount": rollover_amount,
                "total_principal": new_principal,
                "cash_given_to_client": round(cash_given_to_client, 2),
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
            SELECT l.*, c.first_name, c.last_name
            FROM loans l JOIN clients c ON l.client_id = c.id
            WHERE l.id = ?
        """, (loan_id,))
        loan = dict_from_row(c.fetchone())
        if not loan:
            conn.close()
            return None

        # Amortization schedule
        c.execute("""
            SELECT * FROM amortization_schedule
            WHERE loan_id = ? ORDER BY month_number
        """, (loan_id,))
        loan['schedule'] = rows_to_list(c.fetchall())

        # Payments
        c.execute("SELECT * FROM payments WHERE loan_id = ? ORDER BY payment_date DESC",
                  (loan_id,))
        loan['payments'] = rows_to_list(c.fetchall())

        # Total paid
        c.execute("SELECT COALESCE(SUM(amount), 0) FROM payments WHERE loan_id = ?", (loan_id,))
        loan['total_paid'] = c.fetchone()[0]
        loan['remaining'] = round(
            loan['principal'] + loan['total_interest'] - loan['total_paid'], 2
        )

        conn.close()
        return loan

    def get_client_loans(self, client_id):
        """Get all loans for a client."""
        conn = get_connection()
        c = conn.cursor()
        c.execute("""
            SELECT l.*,
                   (SELECT COALESCE(SUM(amount), 0) FROM payments WHERE loan_id = l.id) as total_paid
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
                   (SELECT COALESCE(SUM(amount), 0) FROM payments WHERE loan_id = l.id) as total_paid
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
        conn = get_connection()
        c = conn.cursor()
        c.execute("UPDATE loans SET status = ? WHERE id = ?", (status, loan_id))
        conn.commit()
        conn.close()
        return True

    def extend_loan(self, loan_id, additional_months):
        """
        Extend a loan by adding more months to its term.
        Regenerates the amortization schedule from the remaining balance.
        """
        from loan_engine import generate_amortization_schedule
        conn = get_connection()
        try:
            c = conn.cursor()
            loan_id = int(loan_id)
            additional_months = int(additional_months)
            if additional_months < 1:
                return {"success": False, "error": "Additional months must be at least 1."}

            # Get loan details
            c.execute("SELECT * FROM loans WHERE id = ?", (loan_id,))
            loan = dict_from_row(c.fetchone())
            if not loan:
                return {"success": False, "error": "Loan not found"}

            if loan['status'] != 'active':
                return {"success": False, "error": "Only active loans can be extended"}

            # Calculate total paid
            c.execute("SELECT COALESCE(SUM(amount), 0) FROM payments WHERE loan_id = ?", (loan_id,))
            total_paid = c.fetchone()[0]

            # Remaining balance
            remaining_balance = max(0, loan['principal'] + loan['total_interest'] - total_paid)
            if remaining_balance <= 0:
                return {"success": False, "error": "Loan is already fully paid."}

            # Get the last due date from current schedule
            c.execute("SELECT MAX(due_date), MAX(month_number) FROM amortization_schedule WHERE loan_id = ?",
                      (loan_id,))
            row = c.fetchone()
            last_due_date = row[0] if row[0] else loan['start_date']
            last_month_num = row[1] if row[1] else 0

            new_term = loan['term_months'] + additional_months

            # Build new schedule for additional months using remaining balance
            new_schedule = generate_amortization_schedule(
                remaining_balance, loan['interest_rate'], loan['interest_type'],
                additional_months, last_due_date
            )
            if not new_schedule:
                return {"success": False, "error": "Could not generate additional schedule."}

            # Update loan term
            c.execute("UPDATE loans SET term_months = ? WHERE id = ?", (new_term, loan_id))

            # Append new schedule entries (month numbers continuing from last)
            for i, entry in enumerate(new_schedule):
                c.execute("""
                    INSERT INTO amortization_schedule
                        (loan_id, month_number, due_date, principal_portion,
                         interest_portion, total_due, balance_remaining)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    loan_id, last_month_num + i + 1, entry['due_date'],
                    entry['principal_portion'], entry['interest_portion'],
                    entry['total_due'], entry['balance_remaining']
                ))

            conn.commit()
            app_logger.info("Loan extended: loan_id=%s added %d months", loan_id, additional_months)
            return {"success": True, "new_term": new_term, "additional_months": additional_months}
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
                c.id AS client_id,
                c.first_name,
                c.last_name,
                (SELECT COALESCE(SUM(amount), 0) FROM payments WHERE loan_id = l.id) AS total_paid_on_loan
            FROM payments p
            JOIN loans l ON p.loan_id = l.id
            JOIN clients c ON l.client_id = c.id
            ORDER BY p.payment_date DESC, p.id DESC
            LIMIT ?
        """, (int(limit),))
        rows = rows_to_list(c.fetchall())
        conn.close()

        # Enrich with computed fields
        for r in rows:
            total_due = r['principal'] + r['total_interest']
            remaining = max(0, total_due - r['total_paid_on_loan'])
            months_paid = round(r['total_paid_on_loan'] / r['monthly_payment']) if r['monthly_payment'] > 0 else 0
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
                COALESCE((SELECT SUM(amount) FROM payments WHERE loan_id = l.id), 0) AS total_paid,
                (
                    SELECT COALESCE(SUM(a2.total_due), 0)
                    FROM amortization_schedule a2
                    WHERE a2.loan_id = a.loan_id
                      AND a2.month_number <= a.month_number
                ) AS cumulative_due
            FROM amortization_schedule a
            JOIN loans l ON a.loan_id = l.id
            JOIN clients cl ON l.client_id = cl.id
            WHERE 1 = 1
              {extra_where}
              AND l.status = 'active'
              AND COALESCE((SELECT SUM(amount) FROM payments WHERE loan_id = l.id), 0) < (
                    SELECT COALESCE(SUM(a2.total_due), 0)
                    FROM amortization_schedule a2
                    WHERE a2.loan_id = a.loan_id
                      AND a2.month_number <= a.month_number
              )
            ORDER BY {order_by}
        """, tuple(params))
            rows = rows_to_list(c.fetchall())
        finally:
            conn.close()

        for row in rows:
            outstanding_for_schedule = max(0, row["cumulative_due"] - row["total_paid"])
            row["scheduled_total_due"] = row["total_due"]
            row["total_due"] = round(min(row["total_due"], outstanding_for_schedule), 2)
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
            if amount <= 0:
                raise ValueError("Payment amount must be greater than zero.")
            datetime.strptime(payment_date, "%Y-%m-%d")

            # Check loan before inserting so invalid calls do not leave locks behind.
            c.execute("SELECT principal, total_interest FROM loans WHERE id = ?", (loan_id,))
            loan = c.fetchone()
            if not loan:
                raise ValueError("Loan not found.")
            total_due = loan['principal'] + loan['total_interest']

            c.execute("""
                INSERT INTO payments (loan_id, amount, payment_date, payment_method, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (loan_id, amount, payment_date, method, notes, now))
            payment_id = c.lastrowid  # Capture IMMEDIATELY after INSERT before any SELECT

            # Check if loan is fully paid
            c.execute("SELECT COALESCE(SUM(amount), 0) FROM payments WHERE loan_id = ?", (loan_id,))
            total_paid = c.fetchone()[0]

            if total_paid >= total_due:
                c.execute("UPDATE loans SET status = 'paid' WHERE id = ?", (loan_id,))

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

    def get_payments(self, loan_id):
        """Get all payments for a loan."""
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM payments WHERE loan_id = ? ORDER BY payment_date DESC",
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

    def add_penalty(self, loan_id, client_id, amount, reason, notes="", penalty_date=None):
        """Add a penalty (late payment, missed payment, etc.) to a loan."""
        conn = get_connection()
        c = conn.cursor()
        now = datetime.now().isoformat()
        if not penalty_date:
            penalty_date = datetime.now().strftime("%Y-%m-%d")
        c.execute("""
            INSERT INTO penalties (loan_id, client_id, amount, reason, notes, status, penalty_date, created_at)
            VALUES (?, ?, ?, ?, ?, 'pending', ?, ?)
        """, (int(loan_id), client_id, float(amount), reason, notes, penalty_date, now))
        conn.commit()
        penalty_id = c.lastrowid
        conn.close()
        return penalty_id

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
        conn = get_connection()
        c = conn.cursor()
        c.execute("UPDATE penalties SET status = ? WHERE id = ?", (status, int(penalty_id)))
        conn.commit()
        conn.close()
        return True

    # ═══════════════════════════════════════════════════════════════
    # LOAN ROLLOVER / REFINANCING HELPERS
    # ═══════════════════════════════════════════════════════════════

    def get_loan_rollover_info(self, loan_id):
        """
        Get remaining balance of a loan for rollover/renewal calculations.
        Returns dict with remaining, total_due, already_paid, months_paid,
        monthly_payment, and can_renew (True if >= 3 payments made).
        """
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT principal, total_interest, monthly_payment, term_months FROM loans WHERE id = ?",
                  (int(loan_id),))
        loan = c.fetchone()
        if not loan:
            conn.close()
            return None
        total_due = loan['principal'] + loan['total_interest']
        monthly_payment = loan['monthly_payment'] or 0

        c.execute("SELECT COALESCE(SUM(amount), 0) FROM payments WHERE loan_id = ?",
                  (int(loan_id),))
        paid = c.fetchone()[0]

        # Count discrete payment records (not amount-based)
        c.execute("SELECT COUNT(*) FROM payments WHERE loan_id = ?", (int(loan_id),))
        months_paid = c.fetchone()[0]

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
            SELECT l.id, l.principal, l.total_interest, l.status,
                   (SELECT COALESCE(SUM(amount), 0) FROM payments WHERE loan_id = l.id) as total_paid
            FROM loans l WHERE l.client_id = ? AND l.status = 'active'
            ORDER BY l.created_at DESC LIMIT 1
        """, (client_id,))
        loan = dict_from_row(c.fetchone())
        conn.close()
        if loan:
            loan['remaining'] = round(loan['principal'] + loan['total_interest'] - loan['total_paid'], 2)
        return loan

    def calculate_dti(self, monthly_income, monthly_payment):
        """Calculate debt-to-income ratio as a percentage."""
        if not monthly_income or float(monthly_income) == 0:
            return None
        dti = (float(monthly_payment) / float(monthly_income)) * 100
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
            return {"success": False, "error": "Prêt introuvable"}
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
            return {"success": False, "error": "Prêt introuvable"}
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
            return {"success": False, "error": "Paiement introuvable"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def open_and_print_pdf(self, path):
        """Open a PDF in Preview for native printing."""
        try:
            if os.path.exists(path):
                _open_native(path, app='Preview' if sys.platform == "darwin" else None)
                return {"success": True}
            return {"success": False, "error": "Fichier introuvable"}
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
        conn = get_connection()
        c = conn.cursor()
        for key, value in data.items():
            c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                      (key, str(value)))
        conn.commit()
        conn.close()
        return True

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
            "version": "1.0.0",
            "name": "PH-Lending Pro",
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
        try:
            return db_get_active_profile()
        except Exception as e:
            app_logger.log_exception("get_active_profile_info", e)
            return {"id": "default", "name": "Main Profile", "is_active": True}

    def create_new_profile(self, name, description="", color="#007AFF"):
        """Create a new profile."""
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
        try:
            result = db_switch_profile(profile_id)
            if result:
                init_database()
                app_logger.info("Switched to profile: %s", profile_id)
                return {"success": True}
            return {"success": False, "error": "Profile not found."}
        except Exception as e:
            app_logger.log_exception("switch_active_profile", e)
            return {"success": False, "error": str(e)}

    def rename_existing_profile(self, profile_id, new_name, new_description=None, new_color=None):
        """Rename a profile."""
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

    def set_profile_password(self, password):
        """Set a password for protecting dangerous actions. Stored as SHA-256 hash."""
        try:
            import hashlib
            hashed = hashlib.sha256(password.encode('utf-8')).hexdigest()
            conn = get_connection()
            c = conn.cursor()
            c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('profile_password', ?)", (hashed,))
            c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('password_enabled', 'true')")
            conn.commit()
            conn.close()
            app_logger.info("Profile password has been set.")
            return {"success": True}
        except Exception as e:
            app_logger.log_exception("set_profile_password", e)
            return {"success": False, "error": str(e)}

    def verify_profile_password(self, password):
        """Verify a password against the stored hash."""
        try:
            import hashlib
            hashed = hashlib.sha256(password.encode('utf-8')).hexdigest()
            conn = get_connection()
            c = conn.cursor()
            c.execute("SELECT value FROM settings WHERE key = 'profile_password'")
            row = c.fetchone()
            conn.close()
            if row and row[0] == hashed:
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
            conn.commit()
            conn.close()
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

    # ═══════════════════════════════════════════════════════════════
    # APP LIFECYCLE
    # ═══════════════════════════════════════════════════════════════


    # ═══════════════════════════════════════════════════════════════
    # OVERDUE ALERTS & SMS
    # ═══════════════════════════════════════════════════════════════

    def get_overdue_alerts(self):
        """
        Return all clients with overdue payments (past due date, not yet paid).
        Logic: a client is overdue when total_paid < SUM(installments due by today).
        On-time payers with future installments remaining are NOT flagged.
        """
        conn = get_connection()
        c = conn.cursor()
        today = datetime.now().strftime("%Y-%m-%d")

        # Step 1: Find loans where total paid < total scheduled by today
        c.execute("""
            SELECT
                c.id         AS client_id,
                c.first_name,
                c.last_name,
                c.contact,
                c.rating,
                l.id         AS loan_id,
                l.principal,
                l.interest_rate,
                l.monthly_payment,
                COUNT(a.id)     AS installments_due,
                SUM(a.total_due) AS total_due_so_far,
                COALESCE((
                    SELECT SUM(amount)
                    FROM payments WHERE loan_id = l.id
                ), 0) AS total_paid
            FROM amortization_schedule a
            JOIN loans l ON a.loan_id = l.id
            JOIN clients c ON l.client_id = c.id
            WHERE a.due_date <= ?
              AND l.status   = 'active'
            GROUP BY l.id
            HAVING total_paid < total_due_so_far
        """, (today,))

        rows = rows_to_list(c.fetchall())

        alerts = []
        for r in rows:
            balance_overdue = round(r['total_due_so_far'] - r['total_paid'], 2)
            monthly  = r['monthly_payment']
            loan_id  = r['loan_id']

            # How many installments are fully covered by payments?
            months_covered = int(r['total_paid'] / monthly) if monthly > 0 else 0
            missed_count   = max(1, r['installments_due'] - months_covered)

            # Get the actual due date of the FIRST uncovered installment from the DB
            c.execute("""
                SELECT due_date FROM amortization_schedule
                WHERE loan_id = ? AND due_date <= ?
                ORDER BY due_date ASC
                LIMIT 1 OFFSET ?
            """, (loan_id, today, months_covered))
            row2 = c.fetchone()

            if row2:
                first_unpaid_str = row2['due_date']
                try:
                    first_unpaid_dt = datetime.strptime(first_unpaid_str, "%Y-%m-%d")
                    days_overdue    = max(0, (datetime.now() - first_unpaid_dt).days)
                except Exception:
                    days_overdue = 0
            else:
                days_overdue     = 0
                first_unpaid_str = today

            # Severity tiers
            if days_overdue >= 60:
                severity = 'critical'
            elif days_overdue >= 30:
                severity = 'high'
            elif days_overdue >= 14:
                severity = 'medium'
            else:
                severity = 'low'

            alerts.append({
                'client_id':            r['client_id'],
                'first_name':           r['first_name'],
                'last_name':            r['last_name'],
                'contact':              r['contact'] or '',
                'rating':               r['rating'],
                'loan_id':              loan_id,
                'principal':            round(r['principal'], 2),
                'monthly_payment':      round(monthly, 2),
                'missed_count':         missed_count,
                'total_overdue_amount': balance_overdue,
                'earliest_due':         first_unpaid_str,
                'days_overdue':         days_overdue,
                'severity':             severity,
            })

        conn.close()

        # Sort by most days overdue first
        alerts.sort(key=lambda x: x['days_overdue'], reverse=True)
        return alerts

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
                return {"success": False, "error": "Numéro de téléphone invalide"}

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

            # Format phone number
            clean_phone = ''.join(filter(lambda x: x.isdigit() or x == '+', phone_number))
            if clean_phone.startswith('09'):
                clean_phone = '+63' + clean_phone[1:]
            elif clean_phone.startswith('9') and len(clean_phone) == 10:
                clean_phone = '+63' + clean_phone

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

    def quit_app(self, force_backup=True):
        """
        Gracefully quit the application:
        1. Perform a backup (if not done recently and force_backup=True)
        2. Close the pywebview window
        3. Exit the Python process
        """
        result = {"backup": None, "quitting": True}
        if force_backup:
            try:
                backup_result = backup_local()
                result["backup"] = backup_result
            except Exception as e:
                result["backup_error"] = str(e)

        # Destroy the window (triggers pywebview shutdown loop to exit)
        try:
            if hasattr(self, '_window') and self._window:
                self._window.destroy()
        except Exception:
            pass

        # Force exit in case destroy doesn't fire
        import threading
        def _exit():
            import time
            time.sleep(0.8)
            import os as _os
            _os.kill(_os.getpid(), 9)
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
