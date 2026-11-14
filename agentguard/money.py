"""Money as whole numbers of micro-dollars (millionths of a US dollar).

All amounts in AgentGuard are integers. API prices such as $0.001 add up
exactly, with no floating-point drift. All money is SIMULATED (mock only).
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation

MICROS_PER_USD = 1_000_000


def usd(value: str | int | Decimal) -> int:
    """Convert a dollar amount to integer micro-dollars.

    Floats are rejected on purpose: ``usd(0.1)`` would carry binary error.
    Pass a string instead: ``usd("0.10")``.
    """
    if isinstance(value, bool) or isinstance(value, float):
        raise TypeError("pass dollars as str, int or Decimal, never float")
    try:
        micros = Decimal(str(value)) * MICROS_PER_USD
    except InvalidOperation as exc:
        raise ValueError(f"not a dollar amount: {value!r}") from exc
    if micros != micros.to_integral_value():
        raise ValueError(f"more precision than one micro-dollar: {value!r}")
    return int(micros)


def fmt_usd(micros: int) -> str:
    """Format micro-dollars for display: always exactly two decimals, rounded half up.

    Amounts are stored to the micro-dollar; only the display is rounded, so sub-cent API prices
    (for example $0.002) show as $0.00 while the ledger keeps the exact value."""
    from decimal import ROUND_HALF_UP
    dollars = (Decimal(micros) / MICROS_PER_USD).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    sign = "-" if dollars < 0 else ""
    return f"{sign}${abs(dollars):,.2f}"
