from typing import Any

from ..auth import get_user_id
from ..database import get_repository
from ..handler_utils import (
    api_handler,
    get_path_uuid,
    get_query_date,
    get_route_key,
    model_data,
    parse_json_body,
)
from ..models.income import ExpectedIncome
from ..repositories.financial_repository import RecordNotFoundError
from ..responses import error_response, json_response, no_content_response


@api_handler
def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    del context
    user_id = get_user_id(event)
    route_key = get_route_key(event)
    repository = get_repository()

    if route_key == "POST /income":
        body = parse_json_body(event)
        body.pop("income_id", None)
        income = ExpectedIncome.model_validate(body)
        repository.create_income(user_id, income)
        return json_response(201, model_data(income))

    if route_key == "GET /income":
        start_date = get_query_date(event, "startDate")
        end_date = get_query_date(event, "endDate")
        income_records = repository.list_income(user_id, start_date, end_date)
        return json_response(200, [model_data(income) for income in income_records])

    if route_key == "GET /income/{incomeId}":
        income_id = get_path_uuid(event, "incomeId")
        income = repository.get_income(user_id, income_id)
        if income is None:
            raise RecordNotFoundError("income does not exist")
        return json_response(200, model_data(income))

    if route_key == "PUT /income/{incomeId}":
        income_id = get_path_uuid(event, "incomeId")
        body = parse_json_body(event)
        body["income_id"] = income_id
        income = ExpectedIncome.model_validate(body)
        repository.update_income(user_id, income)
        return json_response(200, model_data(income))

    if route_key == "DELETE /income/{incomeId}":
        income_id = get_path_uuid(event, "incomeId")
        if not repository.delete_income(user_id, income_id):
            raise RecordNotFoundError("income does not exist")
        return no_content_response()

    return error_response(404, "ROUTE_NOT_FOUND", "route does not exist")
