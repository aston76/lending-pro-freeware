"""
PH-Lending Pro — Loan Calculation Engine
Supports fixed-rate and declining-balance interest calculations.
Generates full amortization schedules.
"""

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


def calculate_fixed_interest(principal, rate, term_months):
    """
    Fixed flat interest: rate is the TOTAL rate for the full term.
    (e.g. 3%/month × 6 months → rate=18%, stored as such in the DB)
    Total Interest = Principal × (Rate / 100)
    Monthly Payment = (Principal + Total Interest) / Term
    """
    total_interest = principal * (rate / 100)
    monthly_payment = (principal + total_interest) / term_months
    return {
        "total_interest": round(total_interest, 2),
        "monthly_payment": round(monthly_payment, 2),
        "total_amount": round(principal + total_interest, 2)
    }


def calculate_declining_interest(principal, rate, term_months):
    """
    Declining balance: interest is recalculated each month on the remaining principal.
    rate is the TOTAL flat rate for the full term → monthly_rate = rate / term_months
    Monthly Principal = Principal / Term
    Monthly Interest(n) = Remaining Balance(n) × (Rate/100/term_months)
    """
    monthly_principal = principal / term_months
    monthly_rate = rate / 100 / term_months  # pro-rata monthly rate from total term rate
    total_interest = 0
    balance = principal

    for _ in range(term_months):
        interest = balance * monthly_rate
        total_interest += interest
        balance -= monthly_principal

    return {
        "total_interest": round(total_interest, 2),
        "monthly_payment": None,  # Varies each month
        "total_amount": round(principal + total_interest, 2)
    }


def generate_amortization_schedule(principal, rate, interest_type, term_months, start_date_str):
    """
    Generate a complete amortization schedule.

    Args:
        principal:      loan amount
        rate:           total flat rate for the full term (e.g. 18 for 3%/month × 6 months)
        interest_type:  'fixed' or 'declining'
        term_months:    number of months
        start_date_str: ISO date string (YYYY-MM-DD)

    Returns:
        list of dicts: month_number, due_date, principal_portion,
                       interest_portion, total_due, balance_remaining
    """
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    schedule = []

    if interest_type == "fixed":
        calc = calculate_fixed_interest(principal, rate, term_months)
        monthly_payment = calc["monthly_payment"]
        total_interest = calc["total_interest"]
        monthly_interest = round(total_interest / term_months, 2)
        monthly_principal = round(monthly_payment - monthly_interest, 2)
        balance = principal

        for month in range(1, term_months + 1):
            due_date = start_date + relativedelta(months=month)

            # Last month: absorb rounding differences so balance = 0
            if month == term_months:
                monthly_principal = round(balance, 2)
                monthly_payment = round(monthly_principal + monthly_interest, 2)
                balance = 0
            else:
                balance = round(balance - monthly_principal, 2)

            schedule.append({
                "month_number": month,
                "due_date": due_date.strftime("%Y-%m-%d"),
                "principal_portion": monthly_principal,
                "interest_portion": monthly_interest,
                "total_due": round(monthly_principal + monthly_interest, 2),
                "balance_remaining": max(balance, 0)
            })

    elif interest_type == "declining":
        # rate = total term rate; derive the monthly pro-rata rate
        monthly_rate = rate / 100.0 / term_months
        monthly_principal_base = round(principal / term_months, 2)
        balance = principal

        for month in range(1, term_months + 1):
            due_date = start_date + relativedelta(months=month)
            interest = round(balance * monthly_rate, 2)

            # Last month: clear the full remaining balance
            if month == term_months:
                monthly_principal = round(balance, 2)
                balance = 0
            else:
                monthly_principal = monthly_principal_base
                balance = round(balance - monthly_principal, 2)

            total_due = round(monthly_principal + interest, 2)

            schedule.append({
                "month_number": month,
                "due_date": due_date.strftime("%Y-%m-%d"),
                "principal_portion": monthly_principal,
                "interest_portion": interest,
                "total_due": total_due,
                "balance_remaining": max(balance, 0)
            })

    return schedule


def get_loan_summary(principal, rate, interest_type, term_months):
    """
    Quick summary for the loan calculator preview.
    rate = total flat rate for the full term (e.g. 18 for 3%/mo × 6 months).
    Returns dict with total_interest, monthly_payment (or first/last), total_amount.
    """
    if interest_type == "fixed":
        return calculate_fixed_interest(principal, rate, term_months)
    else:
        calc = calculate_declining_interest(principal, rate, term_months)
        # For declining, compute first and last monthly payments
        monthly_principal = round(principal / term_months, 2)
        monthly_rate = rate / 100 / term_months
        first_interest = round(principal * monthly_rate, 2)
        last_balance = principal - monthly_principal * (term_months - 1)
        last_interest = round(last_balance * monthly_rate, 2)

        calc["first_payment"] = round(monthly_principal + first_interest, 2)
        calc["last_payment"] = round(monthly_principal + last_interest, 2)
        calc["monthly_payment"] = calc["first_payment"]  # Show first as default
        return calc
