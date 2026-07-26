"""Currency configuration shared by exports and printable documents."""

from __future__ import annotations


SUPPORTED_CURRENCIES = {
    "PHP", "EUR", "USD", "CHF", "GBP", "CAD", "AUD", "NZD", "JPY",
    "SGD", "HKD", "AED", "SAR", "INR", "THB", "MYR", "IDR", "VND",
    "KRW", "ZAR", "MXN", "BRL",
}
ZERO_DECIMAL_CURRENCIES = {"JPY", "KRW", "VND", "IDR"}


def normalize_currency(code) -> str:
    normalized = str(code or "PHP").strip().upper()
    return normalized if normalized in SUPPORTED_CURRENCIES else "PHP"


def currency_from_connection(connection) -> str:
    row = connection.execute(
        "SELECT value FROM settings WHERE key = 'currency'"
    ).fetchone()
    value = row[0] if row else "PHP"
    return normalize_currency(value)


def format_money(amount, currency_code: str) -> str:
    code = normalize_currency(currency_code)
    decimals = 0 if code in ZERO_DECIMAL_CURRENCIES else 2
    return f"{code} {float(amount or 0):,.{decimals}f}"
