from typing import Any

from ..auth import get_user_id
from ..config import get_settings
from ..database import get_repository, get_s3_client
from ..handler_utils import api_handler, get_path_uuid, get_route_key, model_data, parse_json_body
from ..models.receipt import ReceiptConfirmRequest, ReceiptUploadRequest
from ..repositories.financial_repository import RecordNotFoundError
from ..responses import error_response, json_response, no_content_response
from ..services.receipt_service import PRESIGNED_URL_SECONDS, receipt_object_key, validate_receipt


def _expense_or_404(user_id, expense_id):
    expense = get_repository().get_expense(user_id, expense_id)
    if expense is None:
        raise RecordNotFoundError("expense does not exist")
    return expense


@api_handler
def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    del context
    user_id = get_user_id(event)
    route_key = get_route_key(event)
    expense_id = get_path_uuid(event, "expenseId")
    expense = _expense_or_404(user_id, expense_id)
    settings = get_settings()
    if not settings.receipt_bucket_name:
        raise RuntimeError("RECEIPT_BUCKET_NAME is required")
    s3 = get_s3_client()

    if route_key == "POST /expenses/{expenseId}/receipt-upload":
        request = ReceiptUploadRequest.model_validate(parse_json_body(event))
        extension = validate_receipt(request.filename, request.content_type, request.size_bytes)
        key = receipt_object_key(user_id, expense_id, extension)
        upload = s3.generate_presigned_post(
            Bucket=settings.receipt_bucket_name,
            Key=key,
            Fields={"Content-Type": request.content_type},
            Conditions=[
                {"Content-Type": request.content_type},
                ["content-length-range", 1, 5 * 1024 * 1024],
            ],
            ExpiresIn=PRESIGNED_URL_SECONDS,
        )
        return json_response(200, {
            "upload_url": upload["url"],
            "fields": upload["fields"],
            "receipt_key": key,
            "expires_in": PRESIGNED_URL_SECONDS,
        })

    if route_key == "POST /expenses/{expenseId}/receipt-confirm":
        request = ReceiptConfirmRequest.model_validate(parse_json_body(event))
        safe_user_id = "".join(character for character in user_id if character.isalnum() or character in "-_")
        expected_prefix = f"receipts/{safe_user_id}/{expense_id}/"
        if not request.receipt_key.startswith(expected_prefix):
            raise ValueError("receipt key does not belong to this expense")
        metadata = s3.head_object(Bucket=settings.receipt_bucket_name, Key=request.receipt_key)
        validate_receipt(
            request.receipt_key,
            metadata.get("ContentType", ""),
            metadata.get("ContentLength", 0),
        )
        if expense.receipt_key and expense.receipt_key != request.receipt_key:
            s3.delete_object(Bucket=settings.receipt_bucket_name, Key=expense.receipt_key)
        updated = expense.model_copy(update={"receipt_key": request.receipt_key})
        get_repository().update_expense(user_id, updated)
        return json_response(200, model_data(updated))

    if route_key == "GET /expenses/{expenseId}/receipt":
        if not expense.receipt_key:
            raise RecordNotFoundError("expense has no receipt")
        url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.receipt_bucket_name, "Key": expense.receipt_key},
            ExpiresIn=PRESIGNED_URL_SECONDS,
        )
        return json_response(200, {"download_url": url, "expires_in": PRESIGNED_URL_SECONDS})

    if route_key == "DELETE /expenses/{expenseId}/receipt":
        if not expense.receipt_key:
            raise RecordNotFoundError("expense has no receipt")
        s3.delete_object(Bucket=settings.receipt_bucket_name, Key=expense.receipt_key)
        get_repository().update_expense(user_id, expense.model_copy(update={"receipt_key": None}))
        return no_content_response()

    return error_response(404, "ROUTE_NOT_FOUND", "route does not exist")
