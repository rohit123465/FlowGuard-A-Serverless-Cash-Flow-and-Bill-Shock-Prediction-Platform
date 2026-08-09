from typing import Any

from ..auth import get_user_id
from ..database import get_repository
from ..handler_utils import api_handler, get_query_bool, get_query_date, get_query_int, get_route_key, model_data
from ..models.forecast import ForecastRequest
from ..responses import error_response, json_response
from ..services.risk_feature_service import build_risk_features
from ..services.risk_model_service import load_risk_model, predict_risk


@api_handler
def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    del context
    if get_route_key(event) != "GET /ml/risk":
        return error_response(404, "ROUTE_NOT_FOUND", "route does not exist")
    user_id = get_user_id(event)
    request = ForecastRequest(
        opening_balance_minor=get_query_int(event, "openingBalanceMinor"),
        safety_buffer_minor=get_query_int(event, "safetyBufferMinor"),
        start_date=get_query_date(event, "startDate"),
        end_date=get_query_date(event, "endDate"),
        include_likely_income=get_query_bool(event, "includeLikelyIncome"),
        include_uncertain_income=False,
    )
    repository = get_repository()
    incomes = repository.list_income(user_id, request.start_date, request.end_date)
    expenses = repository.list_expenses(user_id, request.start_date, request.end_date)
    commitments = repository.list_commitments(user_id)
    features = build_risk_features(request, incomes, commitments, expenses)
    return json_response(200, model_data(predict_risk(features, load_risk_model())))
