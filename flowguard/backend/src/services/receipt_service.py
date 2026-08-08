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


def validate_receipt_signature(content_type: str, header: bytes) -> None:
    signatures = {
        "image/jpeg": (b"\xff\xd8\xff",),
        "image/png": (b"\x89PNG\r\n\x1a\n",),
        "application/pdf": (b"%PDF-",),
    }
    expected = signatures.get(content_type)
    if not expected or not any(header.startswith(signature) for signature in expected):
        raise BadRequestError("receipt contents do not match the selected file type")


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
    if size_bytes < 1:
        raise BadRequestError("receipt cannot be empty")
    return expected_extension


def receipt_object_key(user_id: str, expense_id: UUID, extension: str) -> str:
    safe_user_id = "".join(character for character in user_id if character.isalnum() or character in "-_")
    return f"receipts/{safe_user_id}/{expense_id}/{uuid4()}{extension}"
