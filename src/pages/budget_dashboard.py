import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from models.transaction import Transaction, TransactionType
from models.budget_goal import BudgetGoal
from utils.visualizations import (
    create_monthly_spending_chart,
    create_income_vs_expenses_chart,
    create_category_breakdown_pie,
    create_budget_planning_chart,
)


def init_budget_state():
    """Initialize session state variables for budget tracking."""
    if "transactions" not in st.session_state:
        st.session_state.transactions = []
    if "categories" not in st.session_state:
        st.session_state.categories = {
            "income": ["Salary", "Investments", "Other"],
            "expense": [
                "Housing",
                "Food",
                "Transportation",
                "Utilities",
                "Entertainment",
                "Investment",
                "Travel",
                "Education",
            ],
        }
    if "budget_goal" not in st.session_state:
        st.session_state.budget_goal = None


def render_transaction_form():
    """Render the transaction entry form."""
    with st.form("transaction_form"):
        col1, col2 = st.columns(2)

        with col1:
            transaction_type = st.selectbox(
                "Type",
                options=[t.value for t in TransactionType],
                key="transaction_type",
            )

            amount = st.number_input("Amount", min_value=0.01, step=0.01, key="amount")

        with col2:
            category_list = st.session_state.categories[
                "income" if transaction_type == "income" else "expense"
            ]
            category = st.selectbox("Category", options=category_list, key="category")

            description = st.text_input("Description (optional)", key="description")

        if st.form_submit_button("Add Transaction"):
            try:
                transaction = Transaction(
                    amount=amount,
                    type=TransactionType(transaction_type),
                    category=category,
                    description=description,
                    date=datetime.now(),
                )
                st.session_state.transactions.append(transaction)
                st.success("Transaction added successfully!")
            except ValueError as e:
                st.error(f"Error: {str(e)}")


def render_goal_setting():
    """Render the budget goal setting interface."""
    st.subheader("Budget Planning")

    with st.expander(
        "Set Budget Goals", expanded=not bool(st.session_state.budget_goal)
    ):
        col1, col2 = st.columns(2)

        # Column 1: Donut Chart
        with col1:
            # Create a donut chart for current allocations
            if st.session_state.budget_goal:
                fig = go.Figure(
                    data=[
                        go.Pie(
                            values=list(
                                st.session_state.budget_goal.allocations.values()
                            ),
                            labels=list(
                                st.session_state.budget_goal.allocations.keys()
                            ),
                            hole=0.6,
                            textinfo="label+percent",
                            marker_colors=px.colors.qualitative.Set3,
                        )
                    ]
                )
                fig.update_layout(
                    title="Budget Allocation",
                    showlegend=False,
                    annotations=[
                        dict(
                            text=f"{sum(st.session_state.budget_goal.allocations.values()):.1f}%<br>Allocated",
                            x=0.5,
                            y=0.5,
                            font_size=14,
                            showarrow=False,
                        )
                    ],
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Set your budget goals using the sliders")

        # Column 2: Sliders
        with col2:
            allocations = {}
            remaining = 100.0

            for category in st.session_state.categories["expense"]:
                current = 0.0
                if st.session_state.budget_goal:
                    current = float(
                        st.session_state.budget_goal.allocations.get(category, 0.0)
                    )

                value = st.slider(
                    f"{category} (%)",
                    min_value=0.0,
                    max_value=100.0,
                    value=float(current),
                    step=1.0,
                    key=f"goal_{category}",
                )

                if value > 0:
                    allocations[category] = float(value)
                    remaining -= value

            st.info(f"Remaining allocation: {remaining:.1f}%")

            if st.button("Save Budget Goals"):
                try:
                    st.session_state.budget_goal = BudgetGoal(allocations)
                    st.success("Budget goals saved!")
                    # Force a rerun to update the donut chart
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))


def render_budget_planning():
    """Render the budget planning visualization."""
    if not st.session_state.budget_goal:
        return

    st.subheader("Budget Plan")

    # Get latest income transaction for planning
    income_transactions = [
        t for t in st.session_state.transactions if t.type == TransactionType.INCOME
    ]

    if not income_transactions:
        st.warning("Add income to see budget planning")
        return

    latest_income = max(income_transactions, key=lambda t: t.date)

    # Show planned allocations
    col1, col2 = st.columns(2)

    with col1:
        st.metric("Monthly Income", f"${latest_income.amount:.2f}")

        for category, percentage in st.session_state.budget_goal.allocations.items():
            planned_amount = latest_income.amount * (percentage / 100)
            st.metric(f"{category} Budget", f"${planned_amount:.2f}", f"{percentage}%")

    with col2:
        fig = create_budget_planning_chart(
            latest_income.amount, st.session_state.budget_goal
        )
        st.plotly_chart(fig, use_container_width=True)


def render_visualizations():
    """Render budget visualization charts."""
    if not st.session_state.transactions:
        return

    st.subheader("Budget Analytics")

    col1, col2 = st.columns(2)

    with col1:
        # Monthly spending chart
        fig = create_monthly_spending_chart(st.session_state.transactions)
        if fig:
            st.plotly_chart(fig, use_container_width=True)

        # Category breakdown
        fig = create_category_breakdown_pie(st.session_state.transactions)
        if fig:
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Income vs Expenses
        fig = create_income_vs_expenses_chart(st.session_state.transactions)
        if fig:
            st.plotly_chart(fig, use_container_width=True)


def render_budget_dashboard():
    """Main function to render the budget dashboard."""
    st.header("Budget Dashboard")

    init_budget_state()

    # Goal Setting
    render_goal_setting()

    # Transaction Form
    st.subheader("Add New Transaction")
    render_transaction_form()

    # Budget Planning
    render_budget_planning()

    # Visualizations
    render_visualizations()

    # Transaction History
    if st.session_state.transactions:
        st.subheader("Recent Transactions")
        for transaction in reversed(st.session_state.transactions[-5:]):
            with st.expander(
                f"{transaction.date.strftime('%Y-%m-%d %H:%M')} - {transaction.type.value.title()}: ${transaction.amount:.2f}"
            ):
                st.write(f"Category: {transaction.category}")
                if transaction.description:
                    st.write(f"Description: {transaction.description}")
    else:
        st.info("No transactions recorded yet.")
