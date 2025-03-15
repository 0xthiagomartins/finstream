import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from models.budget_goal import BudgetGoal
from components.expense_card import render_expense_card
from typing import Dict
import pandas as pd


def init_budget_state():
    """Initialize session state variables for budget tracking."""
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
    if "monthly_salary" not in st.session_state:
        st.session_state.monthly_salary = 10000.0  # Default salary for demonstration

    # Initialize expenses if not set
    if "expenses" not in st.session_state:
        st.session_state.expenses = {
            "Housing": {
                "Rent": 1200.0,
                "Insurance": 100.0,
                "Maintenance": 200.0,
            },
            "Food": {
                "Groceries": 400.0,
                "Dining Out": 200.0,
            },
            "Transportation": {
                "Gas": 150.0,
                "Car Insurance": 100.0,
                "Public Transit": 50.0,
            },
            "Utilities": {
                "Electricity": 80.0,
                "Water": 40.0,
                "Internet": 60.0,
                "Phone": 70.0,
            },
            "Entertainment": {
                "Streaming Services": 30.0,
                "Movies": 40.0,
                "Hobbies": 80.0,
            },
            "Investment": {
                "Stock Market": 800.0,
                "Emergency Fund": 200.0,
            },
            "Travel": {
                "Vacation Fund": 250.0,
            },
            "Education": {
                "Online Courses": 150.0,
                "Books": 50.0,
            },
        }

    # Initialize default budget goals if not set
    if "budget_goal" not in st.session_state:
        default_allocations = {
            "Housing": 30.0,  # Common rule of thumb for housing
            "Food": 15.0,  # Essential expense
            "Transportation": 10.0,
            "Utilities": 10.0,
            "Entertainment": 5.0,
            "Investment": 20.0,  # Savings/investment
            "Travel": 5.0,
            "Education": 5.0,
        }
        try:
            st.session_state.budget_goal = BudgetGoal(default_allocations)
        except ValueError as e:
            st.error(f"Error setting default budget goals: {str(e)}")
            st.session_state.budget_goal = None


def render_salary_input():
    """Render the salary input section."""
    col1, col2, col3 = st.columns([2, 4, 3])

    with col1:
        st.caption("Monthly Income")

    with col2:
        salary = st.number_input(
            "Monthly Income",
            min_value=0.0,
            value=st.session_state.monthly_salary,
            step=100.0,
            format="%.2f",
            key="salary_input",
            label_visibility="collapsed",
        )

    with col3:
        if st.button("Update"):
            st.session_state.monthly_salary = salary
            st.success("Salary updated!")
            st.rerun()


def update_expenses(category: str, expenses: Dict[str, float]):
    """Update expenses for a category."""
    if "expenses" not in st.session_state:
        st.session_state.expenses = {}
    st.session_state.expenses[category] = expenses
    st.rerun()


def add_expense(category: str, description: str, amount: float):
    """Add a new expense to a category."""
    if "expenses" not in st.session_state:
        st.session_state.expenses = {}
    if category not in st.session_state.expenses:
        st.session_state.expenses[category] = {}

    st.session_state.expenses[category][description] = amount
    st.rerun()


def render_budget_overview():
    """Render the budget overview section with expense cards."""
    if not st.session_state.budget_goal:
        st.warning("Please set your budget goals first in the Budget Goals page")
        return

    if st.session_state.monthly_salary <= 0:
        st.warning("Please set your monthly salary above")
        return

    # Initialize expenses in session state if needed
    if "expenses" not in st.session_state:
        st.session_state.expenses = {}

    # Add section title
    st.markdown("---")  # Horizontal line for visual separation
    st.header("Edit Expenses")
    st.markdown("Manage your expenses for each budget category")

    # Add spacing style
    st.markdown(
        """
        <style>
            div[data-testid="stExpander"] {
                margin-bottom: 1.5rem;
            }
        </style>
    """,
        unsafe_allow_html=True,
    )

    # Create two columns for expense cards
    left_col, right_col = st.columns(2)

    # Distribute cards between columns
    categories = list(st.session_state.budget_goal.allocations.items())
    for i, (category, percentage) in enumerate(categories):
        should_spend = st.session_state.monthly_salary * (percentage / 100)
        current_expenses = st.session_state.expenses.get(category, {})

        # Alternate between left and right columns
        with left_col if i % 2 == 0 else right_col:
            st.markdown(
                "<div style='margin-bottom: 1rem;'></div>", unsafe_allow_html=True
            )
            render_expense_card(
                category=category,
                budget_amount=should_spend,
                expenses=current_expenses,
                on_update=update_expenses,
                on_add=add_expense,
            )


def render_overview_row():
    """Render the overview row with three components."""
    if not st.session_state.budget_goal:
        return

    # Update column proportions to 27.5/45/27.5
    col1, col2, col3 = st.columns([25, 50, 25])

    # Column 1: Expenses Donut Chart (30%)
    with col1:
        st.subheader("Current Expenses")

        # Calculate total expenses by category
        expenses_by_category = {}
        for category, expenses in st.session_state.expenses.items():
            total = sum(expenses.values())
            if total > 0:  # Only include categories with expenses
                expenses_by_category[category] = total

        if expenses_by_category:
            fig = go.Figure(
                data=[
                    go.Pie(
                        values=list(expenses_by_category.values()),
                        labels=list(expenses_by_category.keys()),
                        hole=0.6,
                        textinfo="label+percent",
                        marker_colors=px.colors.qualitative.Set3,
                    )
                ]
            )
            fig.update_layout(
                showlegend=False,
                annotations=[
                    dict(
                        text=f"${sum(expenses_by_category.values()):.2f}",
                        x=0.5,
                        y=0.5,
                        font_size=14,
                        showarrow=False,
                    )
                ],
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No expenses recorded yet")

    # Column 2: Budget Overview Table (40%)
    with col2:
        st.subheader("Overview")

        # Prepare data for the overview table
        overview_data = []
        total_spent = 0
        total_should_spend = 0

        for category, percentage in st.session_state.budget_goal.allocations.items():
            should_spend = st.session_state.monthly_salary * (percentage / 100)
            spent = sum(st.session_state.expenses.get(category, {}).values())
            used_percentage = (spent / should_spend * 100) if should_spend > 0 else 0

            total_spent += spent
            total_should_spend += should_spend

            # Calculate status and color
            status = "🟢" if used_percentage <= 100 else "🔴"

            overview_data.append(
                {
                    "Status": status,
                    "Budget": category,
                    "Spent": spent,
                    "Should Spend": should_spend,
                    "Used": used_percentage,
                    "Remaining": should_spend - spent,
                }
            )

        # Add total row
        total_used = (
            (total_spent / total_should_spend * 100) if total_should_spend > 0 else 0
        )
        overview_data.append(
            {
                "Status": "🟢" if total_used <= 100 else "🔴",
                "Budget": "TOTAL",
                "Spent": total_spent,
                "Should Spend": total_should_spend,
                "Used": total_used,
                "Remaining": total_should_spend - total_spent,
            }
        )

        # Convert to DataFrame and display with enhanced styling
        df = pd.DataFrame(overview_data)

        st.dataframe(
            df,
            column_config={
                "Status": st.column_config.TextColumn(
                    "Status",
                    help="Budget status indicator",
                    width="small",
                ),
                "Budget": st.column_config.TextColumn(
                    "Category",
                    help="Budget category",
                ),
                "Spent": st.column_config.NumberColumn(
                    "Spent",
                    help="Amount spent so far",
                    min_value=0.0,
                    format="$%.2f",
                ),
                "Should Spend": st.column_config.NumberColumn(
                    "Should Spend",
                    help="Budgeted amount",
                    min_value=0.0,
                    format="$%.2f",
                ),
                "Used": st.column_config.ProgressColumn(
                    "Used %",
                    help="Percentage of budget used",
                    format="%.1f%%",
                    min_value=0,
                    max_value=100,
                ),
                "Remaining": st.column_config.NumberColumn(
                    "Remaining",
                    help="Amount left in budget",
                    format="$%.2f",
                ),
            },
            hide_index=True,
            use_container_width=True,
        )

    # Column 3: Should Spend Distribution (30%)
    with col3:
        st.subheader("Goal Distribution")

        # Calculate should spend amounts
        should_spend_by_category = {
            category: st.session_state.monthly_salary * (percentage / 100)
            for category, percentage in st.session_state.budget_goal.allocations.items()
        }

        fig = go.Figure(
            data=[
                go.Pie(
                    values=list(should_spend_by_category.values()),
                    labels=list(should_spend_by_category.keys()),
                    hole=0.6,
                    textinfo="label+percent",
                    marker_colors=px.colors.qualitative.Set3,
                )
            ]
        )
        fig.update_layout(
            showlegend=False,
            annotations=[
                dict(
                    text=f"${sum(should_spend_by_category.values()):.2f}",
                    x=0.5,
                    y=0.5,
                    font_size=14,
                    showarrow=False,
                )
            ],
        )
        st.plotly_chart(fig, use_container_width=True)

    # Add custom CSS for summary metrics
    st.markdown(
        """
        <style>
            [data-testid="metric-container"] {
                background-color: #262730;
                padding: 1rem;
                border-radius: 0.5rem;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            
            [data-testid="metric-container"] > div {
                width: 100%;
            }
            
            [data-testid="metric-container"] label {
                display: flex;
                align-items: center;
                justify-content: center;
                text-transform: uppercase;
                font-size: 0.875rem !important;
                font-weight: 600;
                letter-spacing: 0.05em;
            }
            
            /* Metric value styling */
            [data-testid="metric-container"] div[data-testid="metric-value"] {
                font-size: 1.875rem !important;
                font-weight: 700;
                font-family: 'JetBrains Mono', monospace !important;
            }
            
            /* Delta value styling */
            [data-testid="metric-container"] div[data-testid="metric-delta"] {
                font-size: 0.875rem !important;
                font-weight: 500;
            }
        </style>
    """,
        unsafe_allow_html=True,
    )

    summary_col1, summary_col2, summary_col3 = st.columns(3)

    with summary_col1:
        st.metric(
            "💰 Total Budget",
            f"${total_should_spend:.2f}",
        )
    with summary_col2:
        st.metric(
            "💸 Total Spent",
            f"${total_spent:.2f}",
        )
    with summary_col3:
        total_remaining = total_should_spend - total_spent
        st.metric(
            "✨ Remaining",
            f"${total_remaining:.2f}",
            delta=(
                f"{'Saving' if total_remaining >= 0 else 'Over'} "
                f"{abs((total_remaining/total_should_spend)*100):.1f}% of Total Budget"
                if total_should_spend > 0
                else None
            ),
            delta_color="normal" if total_remaining >= 0 else "inverse",
        )


def render_budget_dashboard():
    """Main function to render the budget dashboard."""

    init_budget_state()

    # Title and Salary Input in the same row
    header_col1, header_col2 = st.columns([5, 2])

    with header_col1:
        st.title("Budget Dashboard")

    with header_col2:
        render_salary_input()

    st.markdown("---")  #
    # Overview Row
    render_overview_row()

    # Budget Overview Section with Cards
    render_budget_overview()
