from typing import Any

from ..auth import get_user_id
from ..database import get_repository
from ..handler_utils import (
    api_handler,
    get_query_bool,
    get_query_date,
    get_query_int,
    get_route_key,
    model_data,
)
from ..models.forecast import ForecastRequest
from ..responses import error_response, json_response
from ..services.forecast_service import calculate_forecast


@api_handler
def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    del context
    user_id = get_user_id(event)
    route_key = get_route_key(event)
    if route_key != "GET /forecast":
        return error_response(404, "ROUTE_NOT_FOUND", "route does not exist")

    request = ForecastRequest(
        opening_balance_minor=get_query_int(event, "openingBalanceMinor"),
        safety_buffer_minor=get_query_int(event, "safetyBufferMinor"),
        start_date=get_query_date(event, "startDate"),
        end_date=get_query_date(event, "endDate"),
        include_likely_income=get_query_bool(event, "includeLikelyIncome"),
        include_uncertain_income=get_query_bool(event, "includeUncertainIncome"),
    )
    repository = get_repository()
    result = calculate_forecast(
        request,
        incomes=repository.list_income(
            user_id,
            request.start_date,
            request.end_date,
        ),
        commitments=repository.list_commitments(user_id),
        expenses=repository.list_expenses(
            user_id,
            request.start_date,
            request.end_date,
        ),
    )
    return json_response(200, model_data(result))
