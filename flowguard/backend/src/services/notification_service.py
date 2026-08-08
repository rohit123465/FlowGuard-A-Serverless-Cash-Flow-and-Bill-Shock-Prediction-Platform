from datetime import date, datetime, timedelta, timezone
from uuid import NAMESPACE_URL, uuid5

from ..models.forecast import ForecastRequest
from ..models.notification import BillShockNotification, BillShockSettings
from ..repositories.financial_repository import FinancialRepository
from .forecast_service import calculate_forecast


def evaluate_bill_shock(
    repository: FinancialRepository,
    user_id: str,
    settings: BillShockSettings,
    run_date: date,
) -> BillShockNotification | None:
    end_date = run_date + timedelta(days=settings.horizon_days - 1)
    request = ForecastRequest(
        opening_balance_minor=settings.opening_balance_minor,
        safety_buffer_minor=settings.safety_buffer_minor,
        start_date=run_date,
        end_date=end_date,
        include_likely_income=settings.include_likely_income,
        include_uncertain_income=False,
    )
    result = calculate_forecast(
        request,
        incomes=repository.list_income(user_id, run_date, end_date),
        commitments=repository.list_commitments(user_id),
        expenses=repository.list_expenses(user_id, run_date, end_date),
    )
    if result.first_shortfall_date is None or result.shortfall_amount_minor <= 0:
        return None
    notification = BillShockNotification(
        notification_id=uuid5(NAMESPACE_URL, f"flowguard:{user_id}:{run_date}"),
        created_at=datetime.now(timezone.utc),
        forecast_start_date=run_date,
        forecast_end_date=end_date,
        first_shortfall_date=result.first_shortfall_date,
        shortfall_amount_minor=result.shortfall_amount_minor,
        minimum_balance_minor=result.minimum_balance_minor,
        safety_buffer_minor=settings.safety_buffer_minor,
    )
    return notification if repository.put_notification(user_id, notification) else None
