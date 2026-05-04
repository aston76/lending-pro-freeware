"""
PH-Lending Pro — Demo Data Generator (v2)
Generates realistic Filipino lending scenarios including:
  - Normal active clients (paying on time)
  - Overdue clients in 4 severity levels (Low / Medium / High / Critical)
  - Fully paid loans
  - Defaulted loans
  - Referral relationships
  - Complete amortization schedules (required for the alert system)
"""

import sys
import random
from datetime import datetime, timedelta
from database import get_connection, set_demo_mode, generate_client_id

# Force UTF-8 on Windows console to avoid 'charmap' codec errors with special characters
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

TODAY = datetime.now().date()


def _months_ago(n):
    return (TODAY - timedelta(days=30 * n)).strftime("%Y-%m-%d")


def _days_ago(n):
    return (TODAY - timedelta(days=n)).strftime("%Y-%m-%d")


def _make_amortization(c, loan_id, principal, rate, term, start_date_str):
    """Insert a full amortization schedule for a loan (fixed interest)."""
    start = datetime.strptime(start_date_str, "%Y-%m-%d")
    monthly_interest = principal * (rate / 100)
    monthly_principal = principal / term
    monthly_total     = monthly_principal + monthly_interest
    balance           = principal

    for i in range(1, term + 1):
        due = (start + timedelta(days=30 * i)).strftime("%Y-%m-%d")
        balance -= monthly_principal
        c.execute("""
            INSERT INTO amortization_schedule
                (loan_id, month_number, due_date, principal_portion,
                 interest_portion, total_due, balance_remaining)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (loan_id, i, due, round(monthly_principal, 2),
              round(monthly_interest, 2), round(monthly_total, 2),
              round(max(0, balance), 2)))

    return round(monthly_total, 2)


def _add_payments(c, loan_id, monthly_payment, start_date_str, months_paid):
    """Insert payment records for the first N months."""
    start = datetime.strptime(start_date_str, "%Y-%m-%d")
    for i in range(1, months_paid + 1):
        pay_date = (start + timedelta(days=30 * i)).strftime("%Y-%m-%d")
        method = random.choice(["cash", "gcash", "bank"])
        c.execute("""
            INSERT INTO payments (loan_id, amount, payment_date, payment_method, notes, created_at)
            VALUES (?, ?, ?, ?, '', ?)
        """, (loan_id, round(monthly_payment, 2), pay_date, method,
              pay_date + " 09:00:00"))


def _add_client(c, cid, first, last, contact, rating=4, notes="", monthly_income=25000, referred_by=None):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ago = _days_ago(random.randint(10, 400))
    c.execute("""
        INSERT INTO clients (id, first_name, last_name, address, contact,
                             rating, referred_by, notes, monthly_income, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (cid, first, last,
          f"Brgy. {random.choice(['Santo Niño','Poblacion','San Roque','Magsaysay'])}, Cebu City",
          contact, rating, referred_by, notes, monthly_income, ago, now))


def _add_loan(c, client_id, principal, rate, term, start_date, status="active"):
    interest = principal * (rate / 100) * term
    monthly_payment = (principal + interest) / term
    now = start_date + " 08:00:00"
    c.execute("""
        INSERT INTO loans (client_id, principal, interest_rate, interest_type,
                           term_months, start_date, status, total_interest,
                           monthly_payment, created_at)
        VALUES (?, ?, ?, 'fixed', ?, ?, ?, ?, ?, ?)
    """, (client_id, principal, rate, term, start_date, status,
          round(interest, 2), round(monthly_payment, 2), now))
    return c.lastrowid, round(monthly_payment, 2)


def generate_demo_data():
    """Generates realistic demo data with overdue alert scenarios."""
    set_demo_mode(True)
    conn = get_connection()
    c = conn.cursor()

    # Check if already populated
    c.execute("SELECT COUNT(*) FROM clients")
    if c.fetchone()[0] > 0:
        print("Demo database already populated.")
        conn.close()
        return

    print("[*] Generating demo data with alert scenarios...")

    # ═══════════════════════════════════════════════════════════════
    # SCENARIO GROUP A — 🟢 LÉGER (5-13 days overdue)
    # Payment missed 8-12 days ago → LOW severity
    # ═══════════════════════════════════════════════════════════════
    print("  -> Group A: Low severity (8-12 days overdue)...")

    # Maria: 0 payments, loan started 38 days ago → 1st installment was due 8 days ago
    _add_client(c, "DEMO-LOW-001", "Maria", "Santos",  "09171234501", rating=4,
                notes="Missing first payment. Usually reliable.", monthly_income=22000)
    lid, mp = _add_loan(c, "DEMO-LOW-001", 15000, 5.0, 6, _days_ago(38))
    _make_amortization(c, lid, 15000, 5.0, 6, _days_ago(38))
    # 0 payments — 1st installment due 8 days ago → LOW

    # Jose: 2 payments, started 82 days ago → 3rd installment due 22 days ago  → MEDIUM but we'll push it to LOW
    _add_client(c, "DEMO-LOW-002", "Jose", "Reyes",    "09181234502", rating=3,
                notes="Paid 2 months on time, then missed the 3rd.", monthly_income=18000)
    lid, mp = _add_loan(c, "DEMO-LOW-002", 20000, 5.0, 12, _days_ago(72))
    _make_amortization(c, lid, 20000, 5.0, 12, _days_ago(72))
    _add_payments(c, lid, mp, _days_ago(72), 2)  # paid months 1&2, month 3 due 12 days ago

    # Ana: 3 payments, started 100 days ago → 4th installment due 10 days ago
    _add_client(c, "DEMO-LOW-003", "Ana", "Garcia",    "09191234503", rating=5,
                notes="Top borrower. Delayed this month due to hospital bill.", monthly_income=40000)
    lid, mp = _add_loan(c, "DEMO-LOW-003", 50000, 3.0, 12, _days_ago(100))
    _make_amortization(c, lid, 50000, 3.0, 12, _days_ago(100))
    _add_payments(c, lid, mp, _days_ago(100), 3)  # months 1-3 paid, month 4 due 10 days ago

    # ═══════════════════════════════════════════════════════════════
    # SCENARIO GROUP B — 🟡 MODÉRÉ (14-29 days overdue)
    # ═══════════════════════════════════════════════════════════════
    print("  -> Group B: Medium severity (14-29 days overdue)...")

    # Roberto: 1 payment, started 50 days ago → 2nd installment due 20 days ago
    _add_client(c, "DEMO-MED-001", "Roberto", "Cruz",  "09201234504", rating=3,
                notes="Missed 2nd payment. Says business is slow.", monthly_income=15000)
    lid, mp = _add_loan(c, "DEMO-MED-001", 30000, 7.0, 12, _days_ago(50))
    _make_amortization(c, lid, 30000, 7.0, 12, _days_ago(50))
    _add_payments(c, lid, mp, _days_ago(50), 1)  # 1st paid, 2nd due 20 days ago

    # Liza: 0 payments, started 44 days ago → 1st installment due 14 days ago
    _add_client(c, "DEMO-MED-002", "Liza", "Mendoza",  "09211234505", rating=2,
                notes="Has a history of late payments. 2nd warning sent.", monthly_income=12000)
    lid, mp = _add_loan(c, "DEMO-MED-002", 10000, 7.0, 6, _days_ago(44))
    _make_amortization(c, lid, 10000, 7.0, 6, _days_ago(44))
    # 0 payments — 1st due 14 days ago

    # Carlos: 1 payment, started 75 days ago → 2nd installment due 15 days ago
    _add_client(c, "DEMO-MED-003", "Carlos", "Dela Cruz", "09221234506", rating=3,
                notes="Paid first month, then stopped.", monthly_income=20000)
    lid, mp = _add_loan(c, "DEMO-MED-003", 25000, 5.0, 6, _days_ago(75))
    _make_amortization(c, lid, 25000, 5.0, 6, _days_ago(75))
    _add_payments(c, lid, mp, _days_ago(75), 1)  # 1 of 2+ due paid, 2nd due 15 days ago

    # ═══════════════════════════════════════════════════════════════
    # SCENARIO GROUP C — 🟠 URGENT / HIGH (30-59 days overdue)
    # ═══════════════════════════════════════════════════════════════
    print("  -> Group C: High severity (30-59 days overdue)...")

    # Federico: 3 paid, 4th due 40 days ago → HIGH
    _add_client(c, "DEMO-HIGH-001", "Federico", "Bautista", "09231234507", rating=2,
                notes="Phone often unreachable. Visited home 2x.", monthly_income=10000)
    lid, mp = _add_loan(c, "DEMO-HIGH-001", 20000, 7.0, 12, _days_ago(160))
    _make_amortization(c, lid, 20000, 7.0, 12, _days_ago(160))
    _add_payments(c, lid, mp, _days_ago(160), 3)  # 3 paid, 4th due 40 days ago → HIGH

    # Elena: 2 paid, 3rd due 35 days ago → HIGH (referred by Maria Santos)
    _add_client(c, "DEMO-HIGH-002", "Elena", "Villanueva", "09241234508", rating=2,
                notes="Referred client. Guarantor is Maria Santos.", monthly_income=18000,
                referred_by="DEMO-LOW-001")
    lid, mp = _add_loan(c, "DEMO-HIGH-002", 15000, 5.0, 12, _days_ago(125))
    _make_amortization(c, lid, 15000, 5.0, 12, _days_ago(125))
    _add_payments(c, lid, mp, _days_ago(125), 2)  # 2 paid, 3rd due 35 days ago

    # Ramon: 1 paid, 2nd due 50 days ago → HIGH
    _add_client(c, "DEMO-HIGH-003", "Ramon", "Aquino",  "09251234509", rating=1,
                notes="Second loan. First one always paid late. High risk.", monthly_income=8000)
    lid, mp = _add_loan(c, "DEMO-HIGH-003", 8000, 7.0, 6, _days_ago(110))
    _make_amortization(c, lid, 8000, 7.0, 6, _days_ago(110))
    _add_payments(c, lid, mp, _days_ago(110), 1)  # 1 paid, 2nd due 50 days ago

    # ═══════════════════════════════════════════════════════════════
    # SCENARIO GROUP D — 🔴 CRITIQUE (60+ days overdue)
    # ═══════════════════════════════════════════════════════════════
    print("  -> Group D: Critical severity (60+ days overdue)...")

    # Antonio: 4 paid, 5th due 90 days ago → CRITICAL
    _add_client(c, "DEMO-CRIT-001", "Antonio", "Ramos", "09261234510", rating=1,
                notes="[CRITICAL] 3 months no response. Address verified Jan 15.", monthly_income=5000)
    lid, mp = _add_loan(c, "DEMO-CRIT-001", 50000, 7.0, 12, _days_ago(210))
    _make_amortization(c, lid, 50000, 7.0, 12, _days_ago(210))
    _add_payments(c, lid, mp, _days_ago(210), 4)  # 4 paid, 5th due 90 days ago

    # Rosario: 5 paid, 6th due 120 days ago → CRITICAL
    _add_client(c, "DEMO-CRIT-002", "Rosario", "Peralta", "09271234511", rating=1,
                notes="[CRITICAL] Restructuring requested. No payment in 4 months.", monthly_income=0)
    lid, mp = _add_loan(c, "DEMO-CRIT-002", 100000, 5.0, 24, _days_ago(270))
    _make_amortization(c, lid, 100000, 5.0, 24, _days_ago(270))
    _add_payments(c, lid, mp, _days_ago(270), 5)  # 5 paid, 6th due 120 days ago

    # Miguel: 3 paid, 4th due 150 days ago → CRITICAL
    _add_client(c, "DEMO-CRIT-003", "Miguel", "Torres", "09281234512", rating=1,
                notes="[CRITICAL] Phone number changed. Home visit planned.", monthly_income=6000)
    lid, mp = _add_loan(c, "DEMO-CRIT-003", 30000, 7.0, 12, _days_ago(240))
    _make_amortization(c, lid, 30000, 7.0, 12, _days_ago(240))
    _add_payments(c, lid, mp, _days_ago(240), 3)  # 3 paid, 4th due 150 days ago

    # Conchita: 0 payments, loan started 210 days ago → CRITICAL + NO PHONE
    _add_client(c, "DEMO-CRIT-004", "Conchita", "Flores", None, rating=1,
                notes="[NO CONTACT] Invalid phone number. Oldest active overdue case.", monthly_income=0)
    lid, mp = _add_loan(c, "DEMO-CRIT-004", 20000, 7.0, 6, _days_ago(270))
    _make_amortization(c, lid, 20000, 7.0, 6, _days_ago(270))
    # 0 payments — max criticality, no phone to test 'no contact' UI

    # ═══════════════════════════════════════════════════════════════
    # SCENARIO GROUP E — ✅ BONS CLIENTS (à jour)
    # ═══════════════════════════════════════════════════════════════
    print("  -> Group E: Good clients (on time)...")

    good_clients = [
        ("DEMO-GOOD-001", "Benjamin", "Tan",       "09291234513", 5, 35000, 25000, 6,  3.0, 3),
        ("DEMO-GOOD-002", "Gloria",   "Reyes",     "09301234514", 5, 50000, 50000, 12, 5.0, 2),
        ("DEMO-GOOD-003", "Ernesto",  "Castillo",  "09311234515", 4, 20000, 20000, 6,  5.0, 1),
        ("DEMO-GOOD-004", "Carmen",   "Lopez",     "09321234516", 5, 45000, 30000, 12, 3.0, 4),
        ("DEMO-GOOD-005", "Danilo",   "Martinez",  "09331234517", 4, 25000, 15000, 6,  5.0, 1),
        ("DEMO-GOOD-006", "Irene",    "Gonzales",  "09341234518", 5, 60000, 100000, 24, 3.0, 3),
        ("DEMO-GOOD-007", "Nena",     "Dela Rosa", "09351234519", 4, 22000, 10000, 6,  7.0, 1),
        ("DEMO-GOOD-008", "Renato",   "Ocampo",    "09361234520", 5, 80000, 80000, 12, 5.0, 5),
    ]

    for cid, fn, ln, phone, rating, income, principal, term, rate, months_paid in good_clients:
        _add_client(c, cid, fn, ln, phone, rating=rating, monthly_income=income)
        # Start the loan so that months_paid payments are due AND paid,
        # and the NEXT payment is about 15 days away (not yet overdue)
        # start = today - (months_paid * 30) - 15 days
        start_days_ago = months_paid * 30 + 15
        start = _days_ago(start_days_ago)
        lid, mp = _add_loan(c, cid, principal, rate, term, start)
        _make_amortization(c, lid, principal, rate, term, start)
        _add_payments(c, lid, mp, start, months_paid)  # Perfectly on time

    # ═══════════════════════════════════════════════════════════════
    # SCENARIO GROUP F — 💰 PRÊTS ENTIÈREMENT REMBOURSÉS
    # ═══════════════════════════════════════════════════════════════
    print("  -> Group F: Fully paid loans...")

    paid_clients = [
        ("DEMO-PAID-001", "Teresita", "Navarro", "09371234521", 5, 30000, 20000, 6,  5.0),
        ("DEMO-PAID-002", "Victor",   "Lim",     "09381234522", 5, 55000, 50000, 12, 3.0),
        ("DEMO-PAID-003", "Natividad","Sison",   "09391234523", 4, 28000, 15000, 3,  7.0),
        ("DEMO-PAID-004", "Alfredo",  "Magno",   "09401234524", 4, 35000, 30000, 6,  5.0),
        ("DEMO-PAID-005", "Lydia",    "Pascual",  "09411234525", 5, 70000, 100000, 12, 3.0),
    ]

    for cid, fn, ln, phone, rating, income, principal, term, rate in paid_clients:
        _add_client(c, cid, fn, ln, phone, rating=rating, monthly_income=income)
        start = _months_ago(term + random.randint(1, 3))
        lid, mp = _add_loan(c, cid, principal, rate, term, start, status="paid")
        _make_amortization(c, lid, principal, rate, term, start)
        _add_payments(c, lid, mp, start, term)  # All months paid

    # ═══════════════════════════════════════════════════════════════
    # SCENARIO GROUP G — ⚡ DÉFAUTS
    # ═══════════════════════════════════════════════════════════════
    print("  -> Group G: Defaulted loans...")

    _add_client(c, "DEMO-DEF-001", "Rodrigo", "Fernandez", "09421234526", rating=1,
                notes="Defaulted after paying 2 months. Left address.", monthly_income=0)
    lid, mp = _add_loan(c, "DEMO-DEF-001", 25000, 7.0, 12, _months_ago(14), status="defaulted")
    _make_amortization(c, lid, 25000, 7.0, 12, _months_ago(14))
    _add_payments(c, lid, mp, _months_ago(14), 2)

    _add_client(c, "DEMO-DEF-002", "Maribel",  "Castro",   "09431234527", rating=1,
                notes="Defaulted. Legal action in progress.", monthly_income=0)
    lid, mp = _add_loan(c, "DEMO-DEF-002", 50000, 5.0, 24, _months_ago(18), status="defaulted")
    _make_amortization(c, lid, 50000, 5.0, 24, _months_ago(18))
    _add_payments(c, lid, mp, _months_ago(18), 4)

    # ═══════════════════════════════════════════════════════════════
    # REFERRAL COMMISSIONS
    # ═══════════════════════════════════════════════════════════════
    print("  → Referral commissions…")
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Elena was referred by Maria (already set), add commission
    c.execute("""
        SELECT id FROM loans WHERE client_id = 'DEMO-HIGH-002' LIMIT 1
    """)
    row = c.fetchone()
    if row:
        c.execute("""
            INSERT INTO referral_commissions
                (referrer_id, referred_id, loan_id, commission_amount, status, created_at)
            VALUES ('DEMO-LOW-001', 'DEMO-HIGH-002', ?, 750, 'pending', ?)
        """, (row['id'], now_str))

    # Good client referral
    _add_client(c, "DEMO-REF-001", "Maricel", "Bernal", "09441234528", rating=4,
                monthly_income=22000, referred_by="DEMO-GOOD-002")
    lid, mp = _add_loan(c, "DEMO-REF-001", 20000, 5.0, 12, _months_ago(3))
    _make_amortization(c, lid, 20000, 5.0, 12, _months_ago(3))
    _add_payments(c, lid, mp, _months_ago(3), 3)
    c.execute("""
        INSERT INTO referral_commissions
            (referrer_id, referred_id, loan_id, commission_amount, status, created_at)
        VALUES ('DEMO-GOOD-002', 'DEMO-REF-001', ?, 400, 'paid', ?)
    """, (lid, now_str))

    # ═══════════════════════════════════════════════════════════════
    # PENALTIES for some late payers
    # ═══════════════════════════════════════════════════════════════
    print("  → Penalties…")

    penalty_cases = [
        ("DEMO-HIGH-001", 500,  "late_payment",   "pending"),
        ("DEMO-HIGH-001", 500,  "late_payment",   "pending"),
        ("DEMO-HIGH-002", 300,  "late_payment",   "pending"),
        ("DEMO-CRIT-001", 1000, "late_payment",   "pending"),
        ("DEMO-CRIT-001", 1000, "missed_payment", "pending"),
        ("DEMO-CRIT-002", 2000, "missed_payment", "pending"),
        ("DEMO-CRIT-002", 2000, "missed_payment", "pending"),
        ("DEMO-CRIT-003", 500,  "late_payment",   "waived"),
        ("DEMO-MED-001",  300,  "late_payment",   "pending"),
        ("DEMO-MED-002",  200,  "late_payment",   "paid"),
    ]

    for cid, amount, reason, status in penalty_cases:
        c.execute("SELECT id FROM loans WHERE client_id = ? LIMIT 1", (cid,))
        row = c.fetchone()
        if not row:
            continue
        pen_date = _days_ago(random.randint(5, 60))
        c.execute("""
            INSERT INTO penalties (loan_id, client_id, amount, reason, notes, status, penalty_date, created_at)
            VALUES (?, ?, ?, ?, '', ?, ?, ?)
        """, (row['id'], cid, amount, reason, status, pen_date, pen_date + " 08:00:00"))

    conn.commit()
    conn.close()

    # Count what we generated
    conn2 = get_connection()
    c2 = conn2.cursor()
    c2.execute("SELECT COUNT(*) FROM clients")
    nc = c2.fetchone()[0]
    c2.execute("SELECT COUNT(*) FROM loans")
    nl = c2.fetchone()[0]
    c2.execute("SELECT COUNT(*) FROM amortization_schedule")
    na = c2.fetchone()[0]
    c2.execute("SELECT COUNT(*) FROM payments")
    np_ = c2.fetchone()[0]
    conn2.close()

    print(f"""
[OK] Demo data generated!
   Clients  : {nc}
   Loans    : {nl}
   Schedule : {na} entries
   Payments : {np_}

[ALERTS] 10 overdue clients:
   [CRITICAL] 60+ days overdue:
      DEMO-CRIT-001  Antonio Ramos     -  60d - P50,000    - 09261234510
      DEMO-CRIT-002  Rosario Peralta   -  90d - P100,000   - 09271234511
      DEMO-CRIT-003  Miguel Torres     - 120d - P30,000    - 09281234512
      DEMO-CRIT-004  Conchita Flores   - 240d - P20,000    - No phone
   [HIGH] 30-59 days overdue:
      DEMO-HIGH-001  Federico Bautista -  40d - P20,000    - 09231234507
      DEMO-HIGH-002  Elena Villanueva  -  35d - P15,000    - 09241234508
      DEMO-HIGH-003  Ramon Aquino      -  50d - P8,000     - 09251234509
   [MEDIUM] 14-29 days overdue:
      DEMO-MED-001   Roberto Cruz      -  20d - P30,000    - 09201234504
      DEMO-MED-002   Liza Mendoza      -  14d - P10,000    - 09211234505
   [LOW] < 14 days overdue:
      DEMO-LOW-001   Maria Santos      -   8d - P15,000    - 09171234501
""")


if __name__ == '__main__':
    try:
        generate_demo_data()
    except Exception as e:
        import traceback
        print("Demo generation failed:", e)
        traceback.print_exc()
