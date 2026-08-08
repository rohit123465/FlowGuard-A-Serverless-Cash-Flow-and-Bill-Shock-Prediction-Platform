from typing import Any

from ..auth import get_user_id
from ..database import get_repository
from ..handler_utils import api_handler, get_path_uuid, get_route_key, model_data, parse_json_body
from ..models.notification import BillShockSettings
from ..repositories.financial_repository import RecordNotFoundError
from ..responses import error_response, json_response, no_content_response


@api_handler
def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    del context
    user_id = get_user_id(event)
    route_key = get_route_key(event)
    repository = get_repository()

    if route_key == "GET /notifications/settings":
        return json_response(200, model_data(repository.get_bill_shock_settings(user_id)))

    if route_key == "PUT /notifications/settings":
        settings = BillShockSettings.model_validate(parse_json_body(event))
        repository.put_bill_shock_settings(user_id, settings)
        return json_response(200, model_data(settings))

    if route_key == "GET /notifications":
        return json_response(
            200,
            [model_data(item) for item in repository.list_notifications(user_id)[:20]],
        )

    if route_key == "PUT /notifications/{notificationId}/read":
        notification_id = get_path_uuid(event, "notificationId")
        if not repository.mark_notification_read(user_id, notification_id):
            raise RecordNotFoundError("notification does not exist")
        return no_content_response()

    return error_response(404, "ROUTE_NOT_FOUND", "route does not exist")
