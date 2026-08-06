from typing import Any


class AuthenticationError(Exception):
    """Raised when an authenticated Cognito user cannot be identified."""


def get_user_id(event: dict[str, Any]) -> str:
    try:
        user_id = event["requestContext"]["authorizer"]["jwt"]["claims"]["sub"]
    except (KeyError, TypeError) as exc:
        raise AuthenticationError("authenticated user is missing") from exc

    if not isinstance(user_id, str) or not user_id.strip():
        raise AuthenticationError("authenticated user is invalid")

    return user_id.strip()
