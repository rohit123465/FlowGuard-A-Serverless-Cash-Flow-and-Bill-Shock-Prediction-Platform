from datetime import date

from src.services.textract_service import parse_expense_analysis


def _field(field_type: str, value: str, confidence: float) -> dict:
    return {
        "Type": {"Text": field_type},
        "ValueDetection": {"Text": value, "Confidence": confidence},
    }


def test_textract_summary_is_normalised_for_expense_review() -> None:
    result = parse_expense_analysis({
        "AnalyzeExpenseModelVersion": "1.0",
        "ExpenseDocuments": [{"SummaryFields": [
            _field("VENDOR_NAME", "Tesco", 98.2),
            _field("INVOICE_RECEIPT_DATE", "09/08/2026", 94.1),
            _field("TOTAL", "£42.50", 99.0),
        ]}],
    })
    assert result.vendor_name == "Tesco"
    assert result.receipt_date == date(2026, 8, 9)
    assert result.total_minor == 4_250
    assert result.total_confidence == 99.0


def test_textract_uses_highest_confidence_and_does_not_treat_foreign_total_as_gbp() -> None:
    result = parse_expense_analysis({"ExpenseDocuments": [{"SummaryFields": [
        _field("VENDOR_NAME", "Wrong", 40),
        _field("VENDOR_NAME", "Correct", 95),
        _field("TOTAL", "$20.00", 99),
        _field("INVOICE_RECEIPT_DATE", "unclear", 30),
    ]}]})
    assert result.vendor_name == "Correct"
    assert result.total_minor is None
    assert result.total_text == "$20.00"
    assert result.receipt_date is None


def test_empty_textract_result_returns_empty_suggestions() -> None:
    result = parse_expense_analysis({"ExpenseDocuments": []})
    assert result.vendor_name is None
    assert result.receipt_date is None
    assert result.total_minor is None
