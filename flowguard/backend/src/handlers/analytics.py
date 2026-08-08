from calendar import monthrange
from datetime import date
from typing import Any

from ..auth import get_user_id
from ..database import get_repository
from ..handler_utils import api_handler, get_query_int, get_route_key, model_data
from ..responses import error_response, json_response
from ..services.analytics_service import calculate_monthly_analytics


@api_handler
def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    del context
    if get_route_key(event) != "GET /analytics/monthly":
        return error_response(404, "ROUTE_NOT_FOUND", "route does not exist")
    user_id = get_user_id(event)
    year = get_query_int(event, "year")
    month = get_query_int(event, "month")
    if year < 2000 or year > 2100 or month < 1 or month > 12:
        raise ValueError("year or month is outside the supported range")
    start_date = date(year, month, 1)
    end_date = date(year, month, monthrange(year, month)[1])
    repository = get_repository()
    analytics = calculate_monthly_analytics(
        year,
        month,
        repository.list_expenses(user_id, start_date, end_date),
        repository.list_income(user_id, start_date, end_date),
    )
    return json_response(200, model_data(analytics))
