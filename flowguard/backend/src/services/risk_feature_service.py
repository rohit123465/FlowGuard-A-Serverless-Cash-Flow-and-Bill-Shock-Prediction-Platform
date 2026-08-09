from collections.abc import Sequence

from ..models.commitment import Commitment
from ..models.expense import Expense
from ..models.forecast import ForecastRequest
from ..models.income import ExpectedIncome, IncomeConfidence
from ..utils.dates import recurrence_dates


FEATURE_NAMES = (
    "balance_buffer_gap_ratio",
    "guaranteed_income_ratio",
    "likely_income_ratio",
    "expense_outflow_ratio",
    "commitment_outflow_ratio",
    "essential_outflow_ratio",
    "days_to_next_guaranteed_income",
    "scheduled_event_count",
)


def build_risk_features(
    request: ForecastRequest,
    incomes: Sequence[ExpectedIncome],
    commitments: Sequence[Commitment],
    expenses: Sequence[Expense],
) -> dict[str, float]:
    scale = max(abs(request.opening_balance_minor), request.safety_buffer_minor, 10_000)
    guaranteed = [item for item in incomes if item.confidence == IncomeConfidence.GUARANTEED]
    likely = [item for item in incomes if item.confidence == IncomeConfidence.LIKELY]
    commitment_occurrences = [
        (item, due_date)
        for item in commitments
        for due_date in recurrence_dates(item.next_due_date, item.recurrence, request.start_date, request.end_date)
    ]
    expense_total = sum(item.amount_minor for item in expenses)
    commitment_total = sum(item.amount_minor for item, _ in commitment_occurrences)
    essential_total = sum(item.amount_minor for item in expenses if item.essential) + sum(
        item.amount_minor for item, _ in commitment_occurrences if item.essential
    )
    next_guaranteed_days = min(
        ((item.expected_date - request.start_date).days for item in guaranteed),
        default=(request.end_date - request.start_date).days + 1,
    )
    return {
        "balance_buffer_gap_ratio": (request.opening_balance_minor - request.safety_buffer_minor) / scale,
        "guaranteed_income_ratio": sum(item.amount_minor for item in guaranteed) / scale,
        "likely_income_ratio": (
            sum(item.amount_minor for item in likely) / scale
            if request.include_likely_income
            else 0.0
        ),
        "expense_outflow_ratio": expense_total / scale,
        "commitment_outflow_ratio": commitment_total / scale,
        "essential_outflow_ratio": essential_total / scale,
        "days_to_next_guaranteed_income": float(next_guaranteed_days),
        "scheduled_event_count": float(len(incomes) + len(expenses) + len(commitment_occurrences)),
    }
