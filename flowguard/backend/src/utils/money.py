from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


MINOR_UNIT = Decimal("0.01")
MINOR_UNITS_PER_MAJOR = Decimal("100")


def to_minor_units(amount: Decimal | str | int) -> int:
    """Convert a major-unit monetary value, such as pounds, to pennies."""
    if isinstance(amount, bool):
        raise TypeError("amount must be a monetary value")

    try:
        decimal_amount = Decimal(str(amount))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError("amount must be a valid monetary value") from exc

    if not decimal_amount.is_finite():
        raise ValueError("amount must be finite")

    rounded_amount = decimal_amount.quantize(MINOR_UNIT, rounding=ROUND_HALF_UP)
    return int(rounded_amount * MINOR_UNITS_PER_MAJOR)


def from_minor_units(amount_minor: int) -> Decimal:
    """Convert an integer minor-unit value to a two-decimal Decimal."""
    if isinstance(amount_minor, bool) or not isinstance(amount_minor, int):
        raise TypeError("amount_minor must be an integer")

    return (Decimal(amount_minor) / MINOR_UNITS_PER_MAJOR).quantize(MINOR_UNIT)
