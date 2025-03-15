import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
from models.transaction import Transaction, TransactionType
from models.budget_goal import BudgetGoal


def create_monthly_spending_chart(transactions: list[Transaction]):
    """Create a bar chart showing monthly spending by category."""
    if not transactions:
        return None

    # Filter expenses from last 30 days
    thirty_days_ago = datetime.now() - timedelta(days=30)
    expenses = [
        t
        for t in transactions
        if t.type == TransactionType.EXPENSE and t.date >= thirty_days_ago
    ]

    if not expenses:
        return None

    # Create DataFrame
    df = pd.DataFrame(
        [
            {
                "Category": t.category,
                "Amount": t.amount,
                "Date": t.date.strftime("%Y-%m-%d"),
            }
            for t in expenses
        ]
    )

    fig = px.bar(
        df,
        x="Category",
        y="Amount",
        title="Monthly Expenses by Category",
        color="Category",
    )
    return fig


def create_income_vs_expenses_chart(transactions: list[Transaction]):
    """Create a bar chart comparing income vs expenses."""
    if not transactions:
        return None

    # Calculate totals
    income_total = sum(
        t.amount for t in transactions if t.type == TransactionType.INCOME
    )
    expense_total = sum(
        t.amount for t in transactions if t.type == TransactionType.EXPENSE
    )

    fig = go.Figure(
        data=[
            go.Bar(
                x=["Income", "Expenses"],
                y=[income_total, expense_total],
                marker_color=["green", "red"],
            )
        ]
    )
    fig.update_layout(title="Total Income vs Expenses")
    return fig


def create_category_breakdown_pie(transactions: list[Transaction]):
    """Create a pie chart showing expense distribution by category."""
    if not transactions:
        return None

    # Filter expenses
    expenses = [t for t in transactions if t.type == TransactionType.EXPENSE]

    if not expenses:
        return None

    # Group by category
    category_totals = {}
    for t in expenses:
        category_totals[t.category] = category_totals.get(t.category, 0) + t.amount

    fig = px.pie(
        values=list(category_totals.values()),
        names=list(category_totals.keys()),
        title="Expense Distribution by Category",
    )
    return fig


def create_budget_planning_chart(income: float, budget_goal: BudgetGoal):
    """Create a bar chart showing planned budget allocations."""
    categories = []
    amounts = []

    for category, percentage in budget_goal.allocations.items():
        categories.append(category)
        amounts.append(income * (percentage / 100))

    fig = go.Figure(
        data=[
            go.Bar(
                x=categories,
                y=amounts,
                marker_color="lightblue",
            )
        ]
    )

    fig.update_layout(
        title="Planned Monthly Budget",
        yaxis_title="Amount ($)",
        showlegend=False,
    )

    return fig
