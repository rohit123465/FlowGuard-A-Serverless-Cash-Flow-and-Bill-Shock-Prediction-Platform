from collections.abc import Callable
from datetime import date
from typing import Any, TypeVar
from uuid import UUID

from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

from ..models.commitment import Commitment
from ..models.expense import Expense
from ..models.income import ExpectedIncome


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
