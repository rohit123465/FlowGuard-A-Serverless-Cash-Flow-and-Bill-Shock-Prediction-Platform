import calendar
from datetime import date, timedelta

from ..models.commitment import Recurrence


def add_months(value: date, months: int) -> date:
    """Move a date by whole calendar months, clamping to month end."""
    month_index = value.year * 12 + value.month - 1 + months
    year, zero_based_month = divmod(month_index, 12)
    month = zero_based_month + 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def add_years(value: date, years: int) -> date:
    """Move a date by whole calendar years, clamping leap days."""
    day = min(value.day, calendar.monthrange(value.year + years, value.month)[1])
    return date(value.year + years, value.month, day)


def recurrence_dates(
    first_due_date: date,
    recurrence: Recurrence,
    start_date: date,
    end_date: date,
) -> tuple[date, ...]:
    """Return commitment occurrences within an inclusive forecast range."""
    if end_date < start_date:
        raise ValueError("end_date must be on or after start_date")

    if recurrence == Recurrence.ONCE:
        if start_date <= first_due_date <= end_date:
            return (first_due_date,)
        return ()

    occurrences: list[date] = []
    occurrence_index = 0

    while True:
        if recurrence == Recurrence.WEEKLY:
            occurrence = first_due_date + timedelta(weeks=occurrence_index)
        elif recurrence == Recurrence.MONTHLY:
            occurrence = add_months(first_due_date, occurrence_index)
        elif recurrence == Recurrence.YEARLY:
            occurrence = add_years(first_due_date, occurrence_index)
        else:
            raise ValueError(f"unsupported recurrence: {recurrence}")

        if occurrence > end_date:
            break
        if occurrence >= start_date:
            occurrences.append(occurrence)

        occurrence_index += 1

    return tuple(occurrences)
