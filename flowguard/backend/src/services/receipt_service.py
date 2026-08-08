from pathlib import PurePath
from uuid import UUID, uuid4

from ..handler_utils import BadRequestError


ALLOWED_CONTENT_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "application/pdf": ".pdf",
}
MAX_RECEIPT_BYTES = 5 * 1024 * 1024
PRESIGNED_URL_SECONDS = 300


def validate_receipt(filename: str, content_type: str, size_bytes: int) -> str:
    extension = PurePath(filename).suffix.lower()
    expected_extension = ALLOWED_CONTENT_TYPES.get(content_type)
    if not expected_extension:
        raise BadRequestError("receipt must be a JPEG, PNG, or PDF")
    accepted_extensions = {".jpg", ".jpeg"} if content_type == "image/jpeg" else {expected_extension}
    if extension not in accepted_extensions:
        raise BadRequestError("receipt filename does not match its content type")
    if size_bytes > MAX_RECEIPT_BYTES:
        raise BadRequestError("receipt must be 5 MB or smaller")
    return expected_extension


def receipt_object_key(user_id: str, expense_id: UUID, extension: str) -> str:
    safe_user_id = "".join(character for character in user_id if character.isalnum() or character in "-_")
    return f"receipts/{safe_user_id}/{expense_id}/{uuid4()}{extension}"
