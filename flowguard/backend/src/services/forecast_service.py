from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from uuid import UUID, uuid5

from ..models.commitment import Commitment
from ..models.expense import Expense
from ..models.forecast import (
    CashFlowEventType,
    ForecastEvent,
    ForecastRequest,
    ForecastResult,
)
from ..models.income import ExpectedIncome, IncomeConfidence
from ..utils.dates import recurrence_dates


@dataclass(frozen=True, slots=True)
class _PendingEvent:
    event_id: UUID
    event_date: date
    description: str
    event_type: CashFlowEventType
    change_minor: int


def _income_is_included(income: ExpectedIncome, request: ForecastRequest) -> bool:
    if income.confidence == IncomeConfidence.GUARANTEED:
        return True
    if income.confidence == IncomeConfidence.LIKELY:
        return request.include_likely_income
    return request.include_uncertain_income


def _commitment_occurrence_id(commitment_id: UUID, due_date: date) -> UUID:
    return uuid5(commitment_id, due_date.isoformat())


def calculate_forecast(
    request: ForecastRequest,
    incomes: Sequence[ExpectedIncome] = (),
    commitments: Sequence[Commitment] = (),
    expenses: Sequence[Expense] = (),
) -> ForecastResult:
    """Build a conservative, chronological cash-flow forecast."""
    pending_events: list[_PendingEvent] = []
    excluded_income_count = 0

    for income in incomes:
        if not request.start_date <= income.expected_date <= request.end_date:
            continue
        if not _income_is_included(income, request):
            excluded_income_count += 1
            continue

        pending_events.append(
            _PendingEvent(
                event_id=income.income_id,
                event_date=income.expected_date,
                description=income.source,
                event_type=CashFlowEventType.INCOME,
                change_minor=income.amount_minor,
            )
        )

    for commitment in commitments:
        for due_date in recurrence_dates(
            commitment.next_due_date,
            commitment.recurrence,
            request.start_date,
            request.end_date,
        ):
            pending_events.append(
                _PendingEvent(
                    event_id=_commitment_occurrence_id(
                        commitment.commitment_id,
                        due_date,
                    ),
                    event_date=due_date,
                    description=commitment.name,
                    event_type=CashFlowEventType.COMMITMENT,
                    change_minor=-commitment.amount_minor,
                )
            )

    for expense in expenses:
        if request.start_date <= expense.expense_date <= request.end_date:
            pending_events.append(
                _PendingEvent(
                    event_id=expense.expense_id,
                    event_date=expense.expense_date,
                    description=expense.description,
                    event_type=CashFlowEventType.EXPENSE,
                    change_minor=-expense.amount_minor,
                )
            )

    # On the same date, apply outgoings before income for a conservative result.
    pending_events.sort(
        key=lambda event: (
            event.event_date,
            0 if event.change_minor < 0 else 1,
            event.event_type,
            str(event.event_id),
        )
    )

    balance = request.opening_balance_minor
    minimum_balance = balance
    first_shortfall_date = (
        request.start_date
        if balance < request.safety_buffer_minor
        else None
    )
    timeline: list[ForecastEvent] = []

    for event in pending_events:
        balance += event.change_minor
        minimum_balance = min(minimum_balance, balance)

        if balance < request.safety_buffer_minor and first_shortfall_date is None:
            first_shortfall_date = event.event_date

        timeline.append(
            ForecastEvent(
                event_id=event.event_id,
                event_date=event.event_date,
                description=event.description,
                event_type=event.event_type,
                change_minor=event.change_minor,
                projected_balance_minor=balance,
            )
        )

    safe_to_spend = max(
        0,
        minimum_balance - request.safety_buffer_minor,
    )
    shortfall_amount = max(
        0,
        request.safety_buffer_minor - minimum_balance,
    )

    return ForecastResult(
        opening_balance_minor=request.opening_balance_minor,
        safety_buffer_minor=request.safety_buffer_minor,
        safe_to_spend_minor=safe_to_spend,
        minimum_balance_minor=minimum_balance,
        first_shortfall_date=first_shortfall_date,
        shortfall_amount_minor=shortfall_amount,
        excluded_income_count=excluded_income_count,
        timeline=tuple(timeline),
    )
