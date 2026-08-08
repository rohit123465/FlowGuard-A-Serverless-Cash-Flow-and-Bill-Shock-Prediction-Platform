from uuid import UUID

import pytest

from src.handler_utils import BadRequestError
from src.services.receipt_service import receipt_object_key, validate_receipt


@pytest.mark.parametrize(
    ("filename", "content_type", "extension"),
    [
        ("receipt.jpg", "image/jpeg", ".jpg"),
        ("receipt.jpeg", "image/jpeg", ".jpg"),
        ("receipt.png", "image/png", ".png"),
        ("receipt.pdf", "application/pdf", ".pdf"),
    ],
)
def test_receipt_types_are_validated(filename, content_type, extension) -> None:
    assert validate_receipt(filename, content_type, 1024) == extension


def test_receipt_rejects_unsupported_or_oversized_files() -> None:
    with pytest.raises(BadRequestError):
        validate_receipt("receipt.exe", "application/octet-stream", 1024)
    with pytest.raises(BadRequestError):
        validate_receipt("receipt.png", "image/png", 5 * 1024 * 1024 + 1)


def test_receipt_key_is_scoped_to_user_and_expense() -> None:
    expense_id = UUID("0788fd5b-7d67-4494-919a-c61e0eb88219")
    key = receipt_object_key("user/a unsafe", expense_id, ".png")
    assert key.startswith(f"receipts/useraunsafe/{expense_id}/")
    assert key.endswith(".png")
