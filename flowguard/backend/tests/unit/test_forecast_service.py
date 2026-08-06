from datetime import date

import pytest
from pydantic import ValidationError

from src.models.commitment import Commitment, Recurrence
from src.models.expense import Expense
from src.models.forecast import CashFlowEventType, ForecastRequest
from src.models.income import ExpectedIncome, IncomeConfidence
from src.services.forecast_service import calculate_forecast
from src.utils.dates import recurrence_dates


def make_request(**overrides: object) -> ForecastRequest:
    values: dict[str, object] = {
        "opening_balance_minor": 100_000,
        "safety_buffer_minor": 10_000,
        "start_date": date(2026, 8, 1),
        "end_date": date(2026, 8, 31),
    }
    values.update(overrides)
    return ForecastRequest(**values)

#Checks that safe-to-spend is calculated from the lowest predicted balance after bills and income
def test_forecast_calculates_safe_to_spend_from_lowest_balance() -> None:
    result = calculate_forecast(
        make_request(),
        incomes=[
            ExpectedIncome(
                source="Client payment",
                amount_minor=50_000,
                expected_date=date(2026, 8, 15),
            )
        ],
        commitments=[
            Commitment(
                name="Electricity",
                amount_minor=10_000,
                next_due_date=date(2026, 8, 10),
            ),
            Commitment(
                name="Rent",
                amount_minor=80_000,
                next_due_date=date(2026, 8, 20),
            ),
        ],
    )

    assert result.minimum_balance_minor == 60_000
    assert result.safe_to_spend_minor == 50_000
    assert result.first_shortfall_date is None
    assert result.shortfall_amount_minor == 0
    assert [event.projected_balance_minor for event in result.timeline] == [
        90_000,
        140_000,
        60_000,
    ]

#Checks that FlowGuard identifies when the balance first falls below the safety buffer.
def test_forecast_reports_first_shortfall() -> None:
    result = calculate_forecast(
        make_request(opening_balance_minor=80_000),
        commitments=[
            Commitment(
                name="Rent",
                amount_minor=90_000,
                next_due_date=date(2026, 8, 15),
            )
        ],
    )

    assert result.safe_to_spend_minor == 0
    assert result.minimum_balance_minor == -10_000
    assert result.first_shortfall_date == date(2026, 8, 15)
    assert result.shortfall_amount_minor == 20_000

#Ensures uncertain income is not automatically included in the forecast.
def test_uncertain_income_is_excluded_by_default() -> None:
    result = calculate_forecast(
        make_request(),
        incomes=[
            ExpectedIncome(
                source="Possible contract",
                amount_minor=50_000,
                expected_date=date(2026, 8, 12),
                confidence=IncomeConfidence.UNCERTAIN,
            )
        ],
    )

    assert result.safe_to_spend_minor == 90_000
    assert result.excluded_income_count == 1
    assert result.timeline == ()

#Checks that likely income is included when the user enables it.
def test_likely_income_can_be_included_explicitly() -> None:
    result = calculate_forecast(
        make_request(include_likely_income=True),
        incomes=[
            ExpectedIncome(
                source="Likely invoice",
                amount_minor=25_000,
                expected_date=date(2026, 8, 12),
                confidence=IncomeConfidence.LIKELY,
            )
        ],
    )

    assert result.excluded_income_count == 0
    assert len(result.timeline) == 1
    assert result.timeline[0].projected_balance_minor == 125_000

#Ensures monthly bills use valid dates, such as changing 31 January to 28 February.
def test_monthly_commitment_expands_and_clamps_to_month_end() -> None:
    dates = recurrence_dates(
        first_due_date=date(2026, 1, 31),
        recurrence=Recurrence.MONTHLY,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 4, 30),
    )

    assert dates == (
        date(2026, 1, 31),
        date(2026, 2, 28),
        date(2026, 3, 31),
        date(2026, 4, 30),
    )

#Checks that bills are processed before income on the same day to produce a safer forecast.
def test_outgoings_are_applied_before_income_on_the_same_date() -> None:
    shared_date = date(2026, 8, 15)
    result = calculate_forecast(
        make_request(opening_balance_minor=50_000),
        incomes=[
            ExpectedIncome(
                source="Pay",
                amount_minor=100_000,
                expected_date=shared_date,
            )
        ],
        expenses=[
            Expense(
                description="Rent",
                amount_minor=60_000,
                expense_date=shared_date,
                category="housing",
            )
        ],
    )

    assert [event.event_type for event in result.timeline] == [
        CashFlowEventType.EXPENSE,
        CashFlowEventType.INCOME,
    ]
    assert result.minimum_balance_minor == -10_000
    assert result.first_shortfall_date == shared_date

#Ensures transactions outside the selected dates do not affect the forecast.
def test_events_outside_the_forecast_range_are_ignored() -> None:
    result = calculate_forecast(
        make_request(),
        expenses=[
            Expense(
                description="Old expense",
                amount_minor=90_000,
                expense_date=date(2026, 7, 31),
                category="other",
            )
        ],
    )

    assert result.timeline == ()
    assert result.safe_to_spend_minor == 90_000

#Ensures the forecast end date cannot be before its start date.
def test_invalid_forecast_range_is_rejected() -> None:
    with pytest.raises(ValidationError):
        make_request(
            start_date=date(2026, 9, 1),
            end_date=date(2026, 8, 1),
        )

#Ensures adding an expense can never incorrectly increase the amount considered safe to spend.
def test_adding_an_expense_never_increases_safe_to_spend() -> None:
    request = make_request()
    baseline = calculate_forecast(request)
    with_expense = calculate_forecast(
        request,
        expenses=[
            Expense(
                description="Planned purchase",
                amount_minor=20_000,
                expense_date=date(2026, 8, 5),
                category="shopping",
            )
        ],
    )

    assert with_expense.safe_to_spend_minor <= baseline.safe_to_spend_minor
