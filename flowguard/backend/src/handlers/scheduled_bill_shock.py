from datetime import date
from typing import Any

from ..database import get_repository
from ..services.notification_service import evaluate_bill_shock


def handler(event: dict[str, Any], context: Any) -> dict[str, int]:
    del context
    run_date = date.fromisoformat(event["time"][:10]) if event.get("time") else date.today()
    repository = get_repository()
    evaluated = 0
    warnings_created = 0
    for subscription in repository.list_enabled_bill_shock_settings():
        evaluated += 1
        if evaluate_bill_shock(
            repository,
            subscription.user_id,
            subscription.settings,
            run_date,
        ):
            warnings_created += 1
    return {"users_evaluated": evaluated, "warnings_created": warnings_created}
