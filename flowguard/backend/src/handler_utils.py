import base64
import json
import logging
from collections.abc import Callable
from datetime import date
from functools import wraps
from typing import Any, ParamSpec, TypeVar
from uuid import UUID

from pydantic import BaseModel, ValidationError

from .auth import AuthenticationError
from .repositories.financial_repository import (
    RecordAlreadyExistsError,
    RecordNotFoundError,
)
from .responses import error_response


LOGGER = logging.getLogger(__name__)
Parameters = ParamSpec("Parameters")
Response = TypeVar("Response")


class BadRequestError(Exception):
    """Raised when an API request cannot be parsed or validated."""


def api_handler(
    function: Callable[Parameters, dict[str, Any]],
) -> Callable[Parameters, dict[str, Any]]:
    @wraps(function)
    def wrapped(*args: Parameters.args, **kwargs: Parameters.kwargs) -> dict[str, Any]:
        try:
            return function(*args, **kwargs)
        except AuthenticationError as exc:
            return error_response(401, "UNAUTHORIZED", str(exc))
        except (BadRequestError, ValidationError, ValueError) as exc:
            return error_response(400, "BAD_REQUEST", str(exc))
        except RecordNotFoundError as exc:
            return error_response(404, "NOT_FOUND", str(exc))
        except RecordAlreadyExistsError as exc:
            return error_response(409, "CONFLICT", str(exc))
        except Exception:
            LOGGER.exception("Unhandled API error")
            return error_response(500, "INTERNAL_ERROR", "an unexpected error occurred")

    return wrapped


def parse_json_body(event: dict[str, Any]) -> dict[str, Any]:
    body = event.get("body")
    if body is None or body == "":
        raise BadRequestError("request body is required")

    if event.get("isBase64Encoded"):
        try:
            body = base64.b64decode(body).decode("utf-8")
        except (ValueError, UnicodeDecodeError) as exc:
            raise BadRequestError("request body is not valid base64") from exc

    try:
        parsed_body = json.loads(body)
    except (TypeError, json.JSONDecodeError) as exc:
        raise BadRequestError("request body must contain valid JSON") from exc

    if not isinstance(parsed_body, dict):
        raise BadRequestError("request body must be a JSON object")
    return parsed_body


def get_route_key(event: dict[str, Any]) -> str:
    route_key = event.get("routeKey")
    if isinstance(route_key, str) and route_key:
        return route_key

    try:
        method = event["requestContext"]["http"]["method"]
        path = event["rawPath"]
    except (KeyError, TypeError) as exc:
        raise BadRequestError("API route information is missing") from exc
    return f"{method} {path}"


def get_path_uuid(event: dict[str, Any], parameter_name: str) -> UUID:
    try:
        value = event["pathParameters"][parameter_name]
        return UUID(value)
    except (KeyError, TypeError, ValueError) as exc:
        raise BadRequestError(f"{parameter_name} must be a valid UUID") from exc


def get_query_value(event: dict[str, Any], name: str) -> str:
    parameters = event.get("queryStringParameters") or {}
    value = parameters.get(name)
    if not isinstance(value, str) or not value.strip():
        raise BadRequestError(f"query parameter '{name}' is required")
    return value.strip()


def get_query_date(event: dict[str, Any], name: str) -> date:
    value = get_query_value(event, name)
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise BadRequestError(f"query parameter '{name}' must use YYYY-MM-DD") from exc


def get_query_int(event: dict[str, Any], name: str) -> int:
    value = get_query_value(event, name)
    try:
        return int(value)
    except ValueError as exc:
        raise BadRequestError(f"query parameter '{name}' must be an integer") from exc


def get_query_bool(event: dict[str, Any], name: str, default: bool = False) -> bool:
    parameters = event.get("queryStringParameters") or {}
    value = parameters.get(name)
    if value is None:
        return default
    if isinstance(value, str) and value.lower() in {"true", "1"}:
        return True
    if isinstance(value, str) and value.lower() in {"false", "0"}:
        return False
    raise BadRequestError(f"query parameter '{name}' must be true or false")


def model_data(model: BaseModel) -> dict[str, Any]:
    return model.model_dump(mode="json")
