from collections import defaultdict

from ..models.analytics import CategorySpending, MonthlyAnalytics
from ..models.expense import Expense
from ..models.income import ExpectedIncome


def calculate_monthly_analytics(
    year: int,
    month: int,
    expenses: list[Expense],
    income: list[ExpectedIncome],
) -> MonthlyAnalytics:
    total_income = sum(item.amount_minor for item in income)
    total_expenses = sum(item.amount_minor for item in expenses)
    essential = sum(item.amount_minor for item in expenses if item.essential)
    categories: dict[str, int] = defaultdict(int)
    for expense in expenses:
        categories[expense.category] += expense.amount_minor

    breakdown = tuple(
        CategorySpending(
            category=category,
            amount_minor=amount,
            percentage=round(amount / total_expenses * 100, 1)
            if total_expenses
            else 0,
        )
        for category, amount in sorted(
            categories.items(),
            key=lambda item: (-item[1], item[0]),
        )
    )
    net_cash_flow = total_income - total_expenses
    return MonthlyAnalytics(
        year=year,
        month=month,
        total_income_minor=total_income,
        total_expenses_minor=total_expenses,
        essential_expenses_minor=essential,
        discretionary_expenses_minor=total_expenses - essential,
        net_cash_flow_minor=net_cash_flow,
        savings_rate_percent=round(net_cash_flow / total_income * 100, 1)
        if total_income
        else None,
        expense_count=len(expenses),
        income_count=len(income),
        highest_spending_category=breakdown[0].category if breakdown else None,
        category_breakdown=breakdown,
    )
