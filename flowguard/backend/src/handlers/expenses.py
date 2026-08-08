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
from ..models.expense import Expense
from ..repositories.financial_repository import RecordNotFoundError
from ..responses import error_response, json_response, no_content_response


@api_handler
def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    del context
    user_id = get_user_id(event)
    route_key = get_route_key(event)
    repository = get_repository()

    if route_key == "POST /expenses":
        body = parse_json_body(event)
        body.pop("expense_id", None)
        expense = Expense.model_validate(body)
        repository.create_expense(user_id, expense)
        return json_response(201, model_data(expense))

    if route_key == "GET /expenses":
        start_date = get_query_date(event, "startDate")
        end_date = get_query_date(event, "endDate")
        expenses = repository.list_expenses(user_id, start_date, end_date)
        return json_response(200, [model_data(expense) for expense in expenses])

    if route_key == "GET /expenses/{expenseId}":
        expense_id = get_path_uuid(event, "expenseId")
        expense = repository.get_expense(user_id, expense_id)
        if expense is None:
            raise RecordNotFoundError("expense does not exist")
        return json_response(200, model_data(expense))

    if route_key == "PUT /expenses/{expenseId}":
        expense_id = get_path_uuid(event, "expenseId")
        existing = repository.get_expense(user_id, expense_id)
        if existing is None:
            raise RecordNotFoundError("expense does not exist")
        body = parse_json_body(event)
        body["expense_id"] = expense_id
        body["receipt_key"] = existing.receipt_key
        expense = Expense.model_validate(body)
        repository.update_expense(user_id, expense)
        return json_response(200, model_data(expense))

    if route_key == "DELETE /expenses/{expenseId}":
        expense_id = get_path_uuid(event, "expenseId")
        if not repository.delete_expense(user_id, expense_id):
            raise RecordNotFoundError("expense does not exist")
        return no_content_response()

    return error_response(404, "ROUTE_NOT_FOUND", "route does not exist")
