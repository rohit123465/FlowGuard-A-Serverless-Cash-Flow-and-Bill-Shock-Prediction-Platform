from typing import Any

from ..auth import get_user_id
from ..database import get_repository
from ..handler_utils import (
    api_handler,
    get_path_uuid,
    get_route_key,
    model_data,
    parse_json_body,
)
from ..models.commitment import Commitment
from ..repositories.financial_repository import RecordNotFoundError
from ..responses import error_response, json_response, no_content_response


@api_handler
def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    del context
    user_id = get_user_id(event)
    route_key = get_route_key(event)
    repository = get_repository()

    if route_key == "POST /commitments":
        body = parse_json_body(event)
        body.pop("commitment_id", None)
        commitment = Commitment.model_validate(body)
        repository.create_commitment(user_id, commitment)
        return json_response(201, model_data(commitment))

    if route_key == "GET /commitments":
        commitments = repository.list_commitments(user_id)
        return json_response(
            200,
            [model_data(commitment) for commitment in commitments],
        )

    if route_key == "GET /commitments/{commitmentId}":
        commitment_id = get_path_uuid(event, "commitmentId")
        commitment = repository.get_commitment(user_id, commitment_id)
        if commitment is None:
            raise RecordNotFoundError("commitment does not exist")
        return json_response(200, model_data(commitment))

    if route_key == "PUT /commitments/{commitmentId}":
        commitment_id = get_path_uuid(event, "commitmentId")
        body = parse_json_body(event)
        body["commitment_id"] = commitment_id
        commitment = Commitment.model_validate(body)
        repository.update_commitment(user_id, commitment)
        return json_response(200, model_data(commitment))

    if route_key == "DELETE /commitments/{commitmentId}":
        commitment_id = get_path_uuid(event, "commitmentId")
        if not repository.delete_commitment(user_id, commitment_id):
            raise RecordNotFoundError("commitment does not exist")
        return no_content_response()

    return error_response(404, "ROUTE_NOT_FOUND", "route does not exist")
