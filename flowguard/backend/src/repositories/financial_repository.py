from collections.abc import Callable
from datetime import date
from decimal import Decimal
from typing import Any, TypeVar
from uuid import UUID

from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

from ..models.commitment import Commitment
from ..models.expense import Expense
from ..models.income import ExpectedIncome
from ..models.notification import (
    BillShockNotification,
    BillShockSettings,
    EnabledBillShockSettings,
)


FinancialRecord = Expense | ExpectedIncome | Commitment
RecordType = TypeVar("RecordType", Expense, ExpectedIncome, Commitment)


class RecordAlreadyExistsError(Exception):
    """Raised when a record with the same user, type, and ID already exists."""


class RecordNotFoundError(Exception):
    """Raised when a requested financial record does not exist."""

#entityType identifies what kind of financial record an item represents
class FinancialRepository:
    EXPENSE = "EXPENSE"
    INCOME = "INCOME"
    COMMITMENT = "COMMITMENT"
    BILL_SHOCK_SETTINGS_SK = "SETTINGS#BILL_SHOCK"
    NOTIFICATION_PREFIX = "NOTIFICATION#"

    def __init__(self, table: Any) -> None:
        self._table = table

    @staticmethod
    def _user_pk(user_id: str) -> str:
        cleaned_user_id = user_id.strip()
        if not cleaned_user_id:
            raise ValueError("user_id must not be empty")
        return f"USER#{cleaned_user_id}"

    @staticmethod
    def _record_sk(entity_type: str, record_id: UUID) -> str:
        return f"{entity_type}#{record_id}"

    @staticmethod
    def _index_pk(user_pk: str, entity_type: str) -> str:
        return f"{user_pk}#{entity_type}"

    @staticmethod
    def _index_sk(record_date: date, record_id: UUID) -> str:
        return f"{record_date.isoformat()}#{record_id}"

    def _base_item(
        self,
        user_id: str,
        entity_type: str,
        record_id: UUID,
        record_date: date,
    ) -> dict[str, Any]:
        user_pk = self._user_pk(user_id)
        return {
            "PK": user_pk,
            "SK": self._record_sk(entity_type, record_id),
            "GSI1PK": self._index_pk(user_pk, entity_type),
            "GSI1SK": self._index_sk(record_date, record_id),
            "entityType": entity_type,
        }

    def _expense_to_item(self, user_id: str, expense: Expense) -> dict[str, Any]:
        item = self._base_item(
            user_id,
            self.EXPENSE,
            expense.expense_id,
            expense.expense_date,
        )
        item.update(
            {
                "expenseId": str(expense.expense_id),
                "description": expense.description,
                "amountMinor": expense.amount_minor,
                "expenseDate": expense.expense_date.isoformat(),
                "category": expense.category,
                "status": expense.status.value,
                "essential": expense.essential,
            }
        )
        if expense.receipt_key:
            item["receiptKey"] = expense.receipt_key
        return item

    def _income_to_item(self, user_id: str, income: ExpectedIncome) -> dict[str, Any]:
        item = self._base_item(
            user_id,
            self.INCOME,
            income.income_id,
            income.expected_date,
        )
        item.update(
            {
                "incomeId": str(income.income_id),
                "source": income.source,
                "amountMinor": income.amount_minor,
                "expectedDate": income.expected_date.isoformat(),
                "confidence": income.confidence.value,
            }
        )
        return item

    def _commitment_to_item(
        self,
        user_id: str,
        commitment: Commitment,
    ) -> dict[str, Any]:
        item = self._base_item(
            user_id,
            self.COMMITMENT,
            commitment.commitment_id,
            commitment.next_due_date,
        )
        item.update(
            {
                "commitmentId": str(commitment.commitment_id),
                "name": commitment.name,
                "amountMinor": commitment.amount_minor,
                "nextDueDate": commitment.next_due_date.isoformat(),
                "recurrence": commitment.recurrence.value,
                "essential": commitment.essential,
            }
        )
        return item

    @staticmethod
    def _item_to_expense(item: dict[str, Any]) -> Expense:
        return Expense(
            expense_id=item["expenseId"],
            description=item["description"],
            amount_minor=item["amountMinor"],
            expense_date=item["expenseDate"],
            category=item["category"],
            status=item["status"],
            essential=item["essential"],
            receipt_key=item.get("receiptKey"),
        )

    @staticmethod
    def _item_to_income(item: dict[str, Any]) -> ExpectedIncome:
        return ExpectedIncome(
            income_id=item["incomeId"],
            source=item["source"],
            amount_minor=item["amountMinor"],
            expected_date=item["expectedDate"],
            confidence=item["confidence"],
        )

    @staticmethod
    def _item_to_commitment(item: dict[str, Any]) -> Commitment:
        return Commitment(
            commitment_id=item["commitmentId"],
            name=item["name"],
            amount_minor=item["amountMinor"],
            next_due_date=item["nextDueDate"],
            recurrence=item["recurrence"],
            essential=item["essential"],
        )

    def _create(self, item: dict[str, Any]) -> None:
        try:
            self._table.put_item(
                Item=item,
                ConditionExpression="attribute_not_exists(PK) AND attribute_not_exists(SK)",
            )
        except ClientError as exc:
            if exc.response["Error"]["Code"] == "ConditionalCheckFailedException":
                raise RecordAlreadyExistsError("financial record already exists") from exc
            raise

    def _get(
        self,
        user_id: str,
        entity_type: str,
        record_id: UUID,
        converter: Callable[[dict[str, Any]], RecordType],
    ) -> RecordType | None:
        response = self._table.get_item(
            Key={
                "PK": self._user_pk(user_id),
                "SK": self._record_sk(entity_type, record_id),
            },
            ConsistentRead=True,
        )
        item = response.get("Item")
        return converter(item) if item else None

    def _update(self, item: dict[str, Any]) -> None:
        try:
            self._table.put_item(
                Item=item,
                ConditionExpression="attribute_exists(PK) AND attribute_exists(SK)",
            )
        except ClientError as exc:
            if exc.response["Error"]["Code"] == "ConditionalCheckFailedException":
                raise RecordNotFoundError("financial record does not exist") from exc
            raise

    def _delete(self, user_id: str, entity_type: str, record_id: UUID) -> bool:
        response = self._table.delete_item(
            Key={
                "PK": self._user_pk(user_id),
                "SK": self._record_sk(entity_type, record_id),
            },
            ReturnValues="ALL_OLD",
        )
        return "Attributes" in response

    def _query_by_date(
        self,
        user_id: str,
        entity_type: str,
        start_date: date,
        end_date: date,
        converter: Callable[[dict[str, Any]], RecordType],
    ) -> list[RecordType]:
        if end_date < start_date:
            raise ValueError("end_date must be on or after start_date")

        user_pk = self._user_pk(user_id)
        key_condition = Key("GSI1PK").eq(
            self._index_pk(user_pk, entity_type)
        ) & Key("GSI1SK").between(
            f"{start_date.isoformat()}#",
            f"{end_date.isoformat()}#\uffff",
        )
        items: list[dict[str, Any]] = []
        query_arguments: dict[str, Any] = {
            "IndexName": "GSI1",
            "KeyConditionExpression": key_condition,
        }

        while True:
            response = self._table.query(**query_arguments)
            items.extend(response.get("Items", []))
            last_evaluated_key = response.get("LastEvaluatedKey")
            if not last_evaluated_key:
                break
            query_arguments["ExclusiveStartKey"] = last_evaluated_key

        return [converter(item) for item in items]

    def _query_by_type(
        self,
        user_id: str,
        entity_type: str,
        converter: Callable[[dict[str, Any]], RecordType],
    ) -> list[RecordType]:
        items: list[dict[str, Any]] = []
        query_arguments: dict[str, Any] = {
            "KeyConditionExpression": Key("PK").eq(self._user_pk(user_id))
            & Key("SK").begins_with(f"{entity_type}#"),
        }

        while True:
            response = self._table.query(**query_arguments)
            items.extend(response.get("Items", []))
            last_evaluated_key = response.get("LastEvaluatedKey")
            if not last_evaluated_key:
                break
            query_arguments["ExclusiveStartKey"] = last_evaluated_key

        return [converter(item) for item in items]

    def create_expense(self, user_id: str, expense: Expense) -> None:
        self._create(self._expense_to_item(user_id, expense))

    def get_expense(self, user_id: str, expense_id: UUID) -> Expense | None:
        return self._get(user_id, self.EXPENSE, expense_id, self._item_to_expense)

    def list_expenses(
        self,
        user_id: str,
        start_date: date,
        end_date: date,
    ) -> list[Expense]:
        return self._query_by_date(
            user_id,
            self.EXPENSE,
            start_date,
            end_date,
            self._item_to_expense,
        )

    def update_expense(self, user_id: str, expense: Expense) -> None:
        self._update(self._expense_to_item(user_id, expense))

    def delete_expense(self, user_id: str, expense_id: UUID) -> bool:
        return self._delete(user_id, self.EXPENSE, expense_id)

    def create_income(self, user_id: str, income: ExpectedIncome) -> None:
        self._create(self._income_to_item(user_id, income))

    def get_income(self, user_id: str, income_id: UUID) -> ExpectedIncome | None:
        return self._get(user_id, self.INCOME, income_id, self._item_to_income)

    def list_income(
        self,
        user_id: str,
        start_date: date,
        end_date: date,
    ) -> list[ExpectedIncome]:
        return self._query_by_date(
            user_id,
            self.INCOME,
            start_date,
            end_date,
            self._item_to_income,
        )

    def update_income(self, user_id: str, income: ExpectedIncome) -> None:
        self._update(self._income_to_item(user_id, income))

    def delete_income(self, user_id: str, income_id: UUID) -> bool:
        return self._delete(user_id, self.INCOME, income_id)

    def create_commitment(self, user_id: str, commitment: Commitment) -> None:
        self._create(self._commitment_to_item(user_id, commitment))

    def get_commitment(
        self,
        user_id: str,
        commitment_id: UUID,
    ) -> Commitment | None:
        return self._get(
            user_id,
            self.COMMITMENT,
            commitment_id,
            self._item_to_commitment,
        )

    def list_commitments(self, user_id: str) -> list[Commitment]:
        return self._query_by_type(
            user_id,
            self.COMMITMENT,
            self._item_to_commitment,
        )

    def update_commitment(self, user_id: str, commitment: Commitment) -> None:
        self._update(self._commitment_to_item(user_id, commitment))

    def delete_commitment(self, user_id: str, commitment_id: UUID) -> bool:
        return self._delete(user_id, self.COMMITMENT, commitment_id)

    def put_bill_shock_settings(self, user_id: str, settings: BillShockSettings) -> None:
        user_pk = self._user_pk(user_id)
        item = {
            "PK": user_pk,
            "SK": self.BILL_SHOCK_SETTINGS_SK,
            "entityType": "BILL_SHOCK_SETTINGS",
            "enabled": settings.enabled,
            "openingBalanceMinor": settings.opening_balance_minor,
            "safetyBufferMinor": settings.safety_buffer_minor,
            "horizonDays": settings.horizon_days,
            "includeLikelyIncome": settings.include_likely_income,
        }
        if settings.enabled:
            item.update({"GSI2PK": "BILL_SHOCK#ENABLED", "GSI2SK": user_pk})
        self._table.put_item(Item=item)

    def get_bill_shock_settings(self, user_id: str) -> BillShockSettings:
        response = self._table.get_item(
            Key={"PK": self._user_pk(user_id), "SK": self.BILL_SHOCK_SETTINGS_SK},
            ConsistentRead=True,
        )
        item = response.get("Item")
        if not item:
            return BillShockSettings()
        return BillShockSettings(
            enabled=item["enabled"],
            opening_balance_minor=item["openingBalanceMinor"],
            safety_buffer_minor=item["safetyBufferMinor"],
            horizon_days=item["horizonDays"],
            include_likely_income=item.get("includeLikelyIncome", False),
        )

    def list_enabled_bill_shock_settings(self) -> list[EnabledBillShockSettings]:
        items: list[dict[str, Any]] = []
        arguments: dict[str, Any] = {
            "IndexName": "GSI2",
            "KeyConditionExpression": Key("GSI2PK").eq("BILL_SHOCK#ENABLED"),
        }
        while True:
            response = self._table.query(**arguments)
            items.extend(response.get("Items", []))
            last_key = response.get("LastEvaluatedKey")
            if not last_key:
                break
            arguments["ExclusiveStartKey"] = last_key
        return [
            EnabledBillShockSettings(
                user_id=item["PK"].removeprefix("USER#"),
                settings=BillShockSettings(
                    enabled=True,
                    opening_balance_minor=item["openingBalanceMinor"],
                    safety_buffer_minor=item["safetyBufferMinor"],
                    horizon_days=item["horizonDays"],
                    include_likely_income=item.get("includeLikelyIncome", False),
                ),
            )
            for item in items
        ]

    def put_notification(self, user_id: str, notification: BillShockNotification) -> bool:
        item = {
            "PK": self._user_pk(user_id),
            "SK": f"{self.NOTIFICATION_PREFIX}{notification.notification_id}",
            "entityType": "BILL_SHOCK_NOTIFICATION",
            "notificationId": str(notification.notification_id),
            "createdAt": notification.created_at.isoformat(),
            "forecastStartDate": notification.forecast_start_date.isoformat(),
            "forecastEndDate": notification.forecast_end_date.isoformat(),
            "firstShortfallDate": notification.first_shortfall_date.isoformat(),
            "shortfallAmountMinor": notification.shortfall_amount_minor,
            "minimumBalanceMinor": notification.minimum_balance_minor,
            "safetyBufferMinor": notification.safety_buffer_minor,
            "riskProbability": Decimal(str(notification.risk_probability)) if notification.risk_probability is not None else None,
            "riskModelVersion": notification.risk_model_version,
            "read": notification.read,
        }
        try:
            self._table.put_item(
                Item=item,
                ConditionExpression="attribute_not_exists(PK) AND attribute_not_exists(SK)",
            )
            return True
        except ClientError as exc:
            if exc.response["Error"]["Code"] == "ConditionalCheckFailedException":
                return False
            raise

    @staticmethod
    def _item_to_notification(item: dict[str, Any]) -> BillShockNotification:
        return BillShockNotification(
            notification_id=item["notificationId"],
            created_at=item["createdAt"],
            forecast_start_date=item["forecastStartDate"],
            forecast_end_date=item["forecastEndDate"],
            first_shortfall_date=item["firstShortfallDate"],
            shortfall_amount_minor=item["shortfallAmountMinor"],
            minimum_balance_minor=item["minimumBalanceMinor"],
            safety_buffer_minor=item["safetyBufferMinor"],
            risk_probability=item.get("riskProbability"),
            risk_model_version=item.get("riskModelVersion"),
            read=item.get("read", False),
        )

    def list_notifications(self, user_id: str) -> list[BillShockNotification]:
        notifications = self._query_by_type(
            user_id,
            self.NOTIFICATION_PREFIX.rstrip("#"),
            self._item_to_notification,
        )
        return sorted(notifications, key=lambda item: item.created_at, reverse=True)

    def mark_notification_read(self, user_id: str, notification_id: UUID) -> bool:
        try:
            self._table.update_item(
                Key={
                    "PK": self._user_pk(user_id),
                    "SK": f"{self.NOTIFICATION_PREFIX}{notification_id}",
                },
                UpdateExpression="SET #read = :true",
                ConditionExpression="attribute_exists(PK) AND attribute_exists(SK)",
                ExpressionAttributeNames={"#read": "read"},
                ExpressionAttributeValues={":true": True},
            )
            return True
        except ClientError as exc:
            if exc.response["Error"]["Code"] == "ConditionalCheckFailedException":
                return False
            raise
