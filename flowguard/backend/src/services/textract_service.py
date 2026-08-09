import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any

from ..models.receipt_analysis import ReceiptAnalysis


def _best_field(summary_fields: list[dict[str, Any]], field_type: str) -> dict[str, Any] | None:
    matching = [field for field in summary_fields if field.get("Type", {}).get("Text") == field_type]
    return max(matching, key=lambda field: field.get("ValueDetection", {}).get("Confidence", 0), default=None)


def _value(field: dict[str, Any] | None) -> tuple[str | None, float | None]:
    if not field:
        return None, None
    detected = field.get("ValueDetection", {})
    return detected.get("Text"), detected.get("Confidence")


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    cleaned = re.sub(r"\s+", " ", value.strip())
    for pattern in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%d/%m/%y", "%d-%m-%y", "%d %b %Y", "%d %B %Y"):
        try:
            return datetime.strptime(cleaned, pattern).date()
        except ValueError:
            continue
    return None


def _parse_gbp_minor(value: str | None) -> int | None:
    if not value or "$" in value or "€" in value:
        return None
    cleaned = re.sub(r"[^0-9,.-]", "", value).replace(",", "")
    try:
        amount = Decimal(cleaned)
    except (InvalidOperation, ValueError):
        return None
    if amount < 0:
        return None
    return int((amount * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def parse_expense_analysis(response: dict[str, Any]) -> ReceiptAnalysis:
    documents = response.get("ExpenseDocuments", [])
    fields = [field for document in documents for field in document.get("SummaryFields", [])]
    vendor, vendor_confidence = _value(_best_field(fields, "VENDOR_NAME"))
    date_text, date_confidence = _value(_best_field(fields, "INVOICE_RECEIPT_DATE"))
    total_text, total_confidence = _value(_best_field(fields, "TOTAL"))
    return ReceiptAnalysis(
        vendor_name=vendor,
        vendor_confidence=vendor_confidence,
        receipt_date=_parse_date(date_text),
        date_text=date_text,
        date_confidence=date_confidence,
        total_minor=_parse_gbp_minor(total_text),
        total_text=total_text,
        total_confidence=total_confidence,
        model_version=response.get("AnalyzeExpenseModelVersion"),
    )
