import json
from typing import Any


JSON_HEADERS = {"Content-Type": "application/json"}


def json_response(status_code: int, data: Any = None) -> dict[str, Any]:
    payload = {"data": data}
    return {
        "statusCode": status_code,
        "headers": JSON_HEADERS,
        "body": json.dumps(payload, separators=(",", ":")),
    }


def error_response(
    status_code: int,
    code: str,
    message: str,
) -> dict[str, Any]:
    return {
        "statusCode": status_code,
        "headers": JSON_HEADERS,
        "body": json.dumps(
            {"error": {"code": code, "message": message}},
            separators=(",", ":"),
        ),
    }


def no_content_response() -> dict[str, Any]:
    return {"statusCode": 204, "headers": {}, "body": ""}
