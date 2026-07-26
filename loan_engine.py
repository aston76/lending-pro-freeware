"""
Lending Pro Freeware loan calculation engine.

The stored interest rate is the total rate for the full loan term. The UI may
accept a monthly rate, but converts it to a term rate before calling this module.
All contractual amounts are rounded to cents with ROUND_HALF_UP and every
schedule is reconciled to its summary totals.
"""

from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from dateutil.relativedelta import relativedelta


MONEY = Decimal("0.01")
HUNDRED = Decimal("100")


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


def _fixed_amounts(principal, rate, term_months):
    principal_value, rate_value, term_value = _validate_terms(
        principal, rate, term_months
    )
    total_interest = _money(principal_value * rate_value / HUNDRED)
    principal_parts = _distribute_decimal(principal_value, term_value)
    interest_parts = _distribute_decimal(total_interest, term_value)
    return principal_value, total_interest, principal_parts, interest_parts


def _declining_amounts(principal, rate, term_months):
    principal_value, rate_value, term_value = _validate_terms(
        principal, rate, term_months
    )
    principal_parts = _distribute_decimal(principal_value, term_value)
    monthly_rate = rate_value / HUNDRED / Decimal(term_value)
    balance = principal_value
    interest_parts = []
    for principal_part in principal_parts:
        interest_parts.append(_money(balance * monthly_rate))
        balance = _money(balance - principal_part)
    total_interest = _money(sum(interest_parts, Decimal("0")))
    return principal_value, total_interest, principal_parts, interest_parts


def calculate_fixed_interest(principal, rate, term_months):
    """
    Calculate flat interest where rate is the total rate for the full term.

    Example: a 3% monthly rate over 6 months is passed as rate=18.
    """
    principal_value, total_interest, principal_parts, interest_parts = _fixed_amounts(
        principal, rate, term_months
    )
    first_payment = principal_parts[0] + interest_parts[0]
    return {
        "total_interest": float(total_interest),
        "monthly_payment": float(first_payment),
        "total_amount": float(_money(principal_value + total_interest)),
    }


def calculate_declining_interest(principal, rate, term_months):
    """
    Calculate declining-balance interest from a total term rate.

    Principal is split over the term and monthly interest is calculated on the
    opening principal balance. Installments therefore decrease over time.
    """
    principal_value, total_interest, principal_parts, interest_parts = _declining_amounts(
        principal, rate, term_months
    )
    return {
        "total_interest": float(total_interest),
        "monthly_payment": None,
        "total_amount": float(_money(principal_value + total_interest)),
        "first_payment": float(principal_parts[0] + interest_parts[0]),
        "last_payment": float(principal_parts[-1] + interest_parts[-1]),
    }


def generate_amortization_schedule(principal, rate, interest_type, term_months, start_date_str):
    """Generate a cent-reconciled monthly amortization schedule."""
    normalized_type = str(interest_type or "").strip().lower()
    if normalized_type == "fixed":
        principal_value, _, principal_parts, interest_parts = _fixed_amounts(
            principal, rate, term_months
        )
    elif normalized_type == "declining":
        principal_value, _, principal_parts, interest_parts = _declining_amounts(
            principal, rate, term_months
        )
    else:
        raise ValueError("Interest type must be fixed or declining.")

    try:
        start_date = datetime.strptime(str(start_date_str), "%Y-%m-%d")
    except (TypeError, ValueError) as exc:
        raise ValueError("Start date must use YYYY-MM-DD format.") from exc

    balance = principal_value
    schedule = []
    for index, (principal_part, interest_part) in enumerate(
        zip(principal_parts, interest_parts), start=1
    ):
        balance = _money(balance - principal_part)
        total_due = _money(principal_part + interest_part)
        schedule.append({
            "month_number": index,
            "due_date": (start_date + relativedelta(months=index)).strftime("%Y-%m-%d"),
            "principal_portion": float(principal_part),
            "interest_portion": float(interest_part),
            "total_due": float(total_due),
            "balance_remaining": float(max(balance, Decimal("0"))),
        })
    return schedule


def get_loan_summary(principal, rate, interest_type, term_months):
    """Return a preview that uses exactly the same values as the schedule."""
    normalized_type = str(interest_type or "").strip().lower()
    if normalized_type == "fixed":
        return calculate_fixed_interest(principal, rate, term_months)
    if normalized_type == "declining":
        result = calculate_declining_interest(principal, rate, term_months)
        result["monthly_payment"] = result["first_payment"]
        return result
    raise ValueError("Interest type must be fixed or declining.")
