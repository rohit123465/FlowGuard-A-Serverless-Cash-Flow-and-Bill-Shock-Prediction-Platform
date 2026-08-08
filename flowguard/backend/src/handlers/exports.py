import csv
import io
from typing import Any

from ..auth import get_user_id
from ..database import get_repository
from ..handler_utils import api_handler, get_query_date, get_route_key
from ..responses import error_response


@api_handler
def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    del context
    if get_route_key(event) != "GET /exports/expenses.csv":
        return error_response(404, "ROUTE_NOT_FOUND", "route does not exist")
    user_id = get_user_id(event)
    start_date = get_query_date(event, "startDate")
    end_date = get_query_date(event, "endDate")
    expenses = get_repository().list_expenses(user_id, start_date, end_date)
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(["Date", "Description", "Category", "Amount GBP", "Status", "Essential", "Receipt attached"])
    for expense in expenses:
        writer.writerow([
            expense.expense_date.isoformat(),
            expense.description,
            expense.category,
            f"{expense.amount_minor / 100:.2f}",
            expense.status.value,
            "Yes" if expense.essential else "No",
            "Yes" if expense.receipt_key else "No",
        ])
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "text/csv; charset=utf-8",
            "Content-Disposition": f'attachment; filename="flowguard-expenses-{start_date}-{end_date}.csv"',
        },
        "body": output.getvalue(),
        "isBase64Encoded": False,
    }
