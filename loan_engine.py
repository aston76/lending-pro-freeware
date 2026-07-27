"""
Lending Pro Freeware loan calculation engine.

The stored interest rate is the total rate for the full loan term. The UI may
accept a monthly rate, but converts it to a term rate before calling this module.
All contractual amounts are rounded to cents with ROUND_HALF_UP and every
schedule is reconciled to its summary totals.
"""

from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from dateutil.relativedelta import relativedelta


MONEY = Decimal("0.01")
HUNDRED = Decimal("100")
FREQUENCIES = {"daily", "weekly", "biweekly", "monthly"}


def _as_decimal(value, field_name):
    try:
        result = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be a valid number.") from exc
    if not result.is_finite():
        raise ValueError(f"{field_name} must be a finite number.")
    return result


def _money(value):
    return value.quantize(MONEY, rounding=ROUND_HALF_UP)


def _validate_terms(principal, rate, term_months):
    principal_value = _as_decimal(principal, "Principal")
    rate_value = _as_decimal(rate, "Interest rate")
    try:
        term_value = int(term_months)
    except (TypeError, ValueError) as exc:
        raise ValueError("Loan term must be a whole number of months.") from exc

    try:
        if Decimal(str(term_months)) != Decimal(term_value):
            raise ValueError("Loan term must be a whole number of months.")
    except InvalidOperation as exc:
        raise ValueError("Loan term must be a whole number of months.") from exc

    if principal_value <= 0:
        raise ValueError("Principal must be greater than zero.")
    if rate_value < 0:
        raise ValueError("Interest rate cannot be negative.")
    if term_value < 1:
        raise ValueError("Loan term must be at least 1 month.")

    return _money(principal_value), rate_value, term_value


def _distribute_decimal(total, count):
    """Distribute a money amount into exact cent values whose sum is total."""
    if int(count) < 1:
        raise ValueError("Distribution count must be at least 1.")
    total_cents = int((_money(total) * 100).to_integral_value())
    sign = -1 if total_cents < 0 else 1
    base, remainder = divmod(abs(total_cents), int(count))
    return [
        Decimal(sign * (base + (1 if index < remainder else 0))) / 100
        for index in range(int(count))
    ]


def distribute_money(total, count):
    """Public cent-safe distribution helper used when rescheduling a loan."""
    total_value = _as_decimal(total, "Amount")
    return [float(value) for value in _distribute_decimal(total_value, int(count))]


def get_installment_count(term_months, repayment_frequency="monthly"):
    """Return the contractual installment count for a duration in months."""
    _, _, term_value = _validate_terms(Decimal("1"), Decimal("0"), term_months)
    frequency = str(repayment_frequency or "monthly").strip().lower()
    if frequency not in FREQUENCIES:
        raise ValueError("Repayment frequency must be daily, weekly, biweekly or monthly.")
    periods_per_year = {
        "daily": Decimal("365"),
        "weekly": Decimal("52"),
        "biweekly": Decimal("26"),
        "monthly": Decimal("12"),
    }[frequency]
    return max(1, int(
        (Decimal(term_value) * periods_per_year / Decimal("12")).quantize(
            Decimal("1"), rounding=ROUND_HALF_UP
        )
    ))


def _fixed_amounts(principal, rate, term_months, installment_count=None):
    principal_value, rate_value, term_value = _validate_terms(
        principal, rate, term_months
    )
    total_interest = _money(principal_value * rate_value / HUNDRED)
    count = int(installment_count or term_value)
    principal_parts = _distribute_decimal(principal_value, count)
    interest_parts = _distribute_decimal(total_interest, count)
    return principal_value, total_interest, principal_parts, interest_parts


def _declining_amounts(principal, rate, term_months, installment_count=None):
    principal_value, rate_value, term_value = _validate_terms(
        principal, rate, term_months
    )
    count = int(installment_count or term_value)
    principal_parts = _distribute_decimal(principal_value, count)
    periodic_rate = rate_value / HUNDRED / Decimal(count)
    balance = principal_value
    interest_parts = []
    for principal_part in principal_parts:
        interest_parts.append(_money(balance * periodic_rate))
        balance = _money(balance - principal_part)
    total_interest = _money(sum(interest_parts, Decimal("0")))
    return principal_value, total_interest, principal_parts, interest_parts


def calculate_fixed_interest(principal, rate, term_months, repayment_frequency="monthly"):
    """
    Calculate flat interest where rate is the total rate for the full term.

    Example: a 3% monthly rate over 6 months is passed as rate=18.
    """
    count = get_installment_count(term_months, repayment_frequency)
    principal_value, total_interest, principal_parts, interest_parts = _fixed_amounts(
        principal, rate, term_months, count
    )
    first_payment = principal_parts[0] + interest_parts[0]
    return {
        "total_interest": float(total_interest),
        "monthly_payment": float(first_payment),
        "installment_amount": float(first_payment),
        "installment_count": count,
        "total_amount": float(_money(principal_value + total_interest)),
    }


def calculate_declining_interest(principal, rate, term_months, repayment_frequency="monthly"):
    """
    Calculate declining-balance interest from a total term rate.

    Principal is split over the term and monthly interest is calculated on the
    opening principal balance. Installments therefore decrease over time.
    """
    count = get_installment_count(term_months, repayment_frequency)
    principal_value, total_interest, principal_parts, interest_parts = _declining_amounts(
        principal, rate, term_months, count
    )
    return {
        "total_interest": float(total_interest),
        "monthly_payment": None,
        "total_amount": float(_money(principal_value + total_interest)),
        "first_payment": float(principal_parts[0] + interest_parts[0]),
        "last_payment": float(principal_parts[-1] + interest_parts[-1]),
        "installment_amount": float(principal_parts[0] + interest_parts[0]),
        "installment_count": count,
    }


def advance_due_date(start_date, index, repayment_frequency):
    if repayment_frequency == "daily":
        return start_date + timedelta(days=index)
    if repayment_frequency == "weekly":
        return start_date + timedelta(days=7 * index)
    if repayment_frequency == "biweekly":
        return start_date + timedelta(days=14 * index)
    return start_date + relativedelta(months=index)


def generate_amortization_schedule(
    principal,
    rate,
    interest_type,
    term_months,
    start_date_str,
    repayment_frequency="monthly",
    interest_deducted_upfront=False,
):
    """Generate a cent-reconciled schedule for the selected frequency."""
    normalized_type = str(interest_type or "").strip().lower()
    frequency = str(repayment_frequency or "monthly").strip().lower()
    count = get_installment_count(term_months, frequency)
    if normalized_type == "fixed":
        principal_value, _, principal_parts, interest_parts = _fixed_amounts(
            principal, rate, term_months, count
        )
    elif normalized_type == "declining":
        principal_value, _, principal_parts, interest_parts = _declining_amounts(
            principal, rate, term_months, count
        )
    else:
        raise ValueError("Interest type must be fixed or declining.")

    try:
        start_date = datetime.strptime(str(start_date_str), "%Y-%m-%d")
    except (TypeError, ValueError) as exc:
        raise ValueError("Start date must use YYYY-MM-DD format.") from exc

    if bool(interest_deducted_upfront):
        interest_parts = [Decimal("0.00") for _ in principal_parts]

    balance = principal_value
    schedule = []
    for index, (principal_part, interest_part) in enumerate(
        zip(principal_parts, interest_parts), start=1
    ):
        balance = _money(balance - principal_part)
        total_due = _money(principal_part + interest_part)
        schedule.append({
            "month_number": index,
            "due_date": advance_due_date(start_date, index, frequency).strftime("%Y-%m-%d"),
            "principal_portion": float(principal_part),
            "interest_portion": float(interest_part),
            "total_due": float(total_due),
            "balance_remaining": float(max(balance, Decimal("0"))),
        })
    return schedule


def _effective_annual_rate(disbursed_amount, schedule, start_date_str):
    """Calculate XIRR-style annual rate from dated borrower cash flows."""
    disbursed = _as_decimal(disbursed_amount, "Disbursed amount")
    if disbursed <= 0 or not schedule:
        raise ValueError("Net disbursed amount must be greater than zero.")
    start_date = datetime.strptime(str(start_date_str), "%Y-%m-%d")

    def npv(rate):
        value = float(disbursed)
        for row in schedule:
            due = datetime.strptime(row["due_date"], "%Y-%m-%d")
            years = max(0, (due - start_date).days) / 365.0
            value -= float(row["total_due"]) / ((1.0 + rate) ** years)
        return value

    low = -0.9999
    high = 1.0
    low_value = npv(low)
    high_value = npv(high)
    while low_value * high_value > 0 and high < 1000000:
        high *= 2
        high_value = npv(high)
    if low_value * high_value > 0:
        return 0.0
    for _ in range(120):
        mid = (low + high) / 2
        mid_value = npv(mid)
        if abs(mid_value) < 0.000001:
            return round(mid * 100, 4)
        if low_value * mid_value <= 0:
            high = mid
        else:
            low = mid
            low_value = mid_value
    return round(((low + high) / 2) * 100, 4)


def get_loan_summary(
    principal,
    rate,
    interest_type,
    term_months,
    repayment_frequency="monthly",
    processing_fee=0,
    insurance_fee=0,
    interest_deducted_upfront=False,
    start_date_str=None,
):
    """Return totals, net disbursement and effective annual percentage rate."""
    normalized_type = str(interest_type or "").strip().lower()
    if normalized_type == "fixed":
        result = calculate_fixed_interest(principal, rate, term_months, repayment_frequency)
    elif normalized_type == "declining":
        result = calculate_declining_interest(principal, rate, term_months, repayment_frequency)
        result["monthly_payment"] = result["first_payment"]
    else:
        raise ValueError("Interest type must be fixed or declining.")

    principal_value = _as_decimal(principal, "Principal")
    processing = _as_decimal(processing_fee or 0, "Processing fee")
    insurance = _as_decimal(insurance_fee or 0, "Insurance fee")
    if processing < 0 or insurance < 0:
        raise ValueError("Loan fees cannot be negative.")
    upfront_interest = Decimal(str(result["total_interest"])) if interest_deducted_upfront else Decimal("0")
    disbursed = _money(principal_value - processing - insurance - upfront_interest)
    if disbursed <= 0:
        raise ValueError("Fees and upfront interest must be lower than the principal.")

    total_repayment = _money(
        principal_value + (Decimal("0") if interest_deducted_upfront else Decimal(str(result["total_interest"])))
    )
    result.update({
        "repayment_frequency": str(repayment_frequency or "monthly").lower(),
        "processing_fee": float(_money(processing)),
        "insurance_fee": float(_money(insurance)),
        "interest_deducted_upfront": bool(interest_deducted_upfront),
        "disbursed_amount": float(disbursed),
        "total_amount": float(total_repayment),
        "total_repayment": float(total_repayment),
    })

    if start_date_str:
        schedule = generate_amortization_schedule(
            principal, rate, interest_type, term_months, start_date_str,
            repayment_frequency, interest_deducted_upfront,
        )
        result["installment_amount"] = schedule[0]["total_due"]
        result["monthly_payment"] = schedule[0]["total_due"]
        result["installment_count"] = len(schedule)
        result["taeg"] = _effective_annual_rate(disbursed, schedule, start_date_str)
    else:
        result["taeg"] = 0.0
    return result
