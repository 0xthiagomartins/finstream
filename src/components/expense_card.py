import streamlit as st
import pandas as pd
from typing import Dict


def render_expense_card(
    category: str,
    budget_amount: float,
    expenses: Dict[str, float],
    on_update: callable,
    on_add: callable,
):
    """Render an expense card for a specific budget category."""
    with st.container(border=True):
        # Card header with category and total amount
        total_spent = sum(expenses.values())
        percentage_used = (
            (total_spent / budget_amount * 100) if budget_amount > 0 else 0
        )

        header_col1, header_col2 = st.columns([2, 2])
        with header_col1:
            st.subheader(category)
        with header_col2:
            st.subheader(rf"{total_spent:.2f} / {budget_amount:.2f}")

        # Progress bar for budget usage
        st.progress(min(percentage_used / 100, 1.0))

        # Expenses table with enhanced styling
        if not expenses:
            st.info("No expenses recorded yet")
        else:
            # Convert expenses to dataframe for easier editing
            df = pd.DataFrame(
                [
                    {"Expense": desc, "Amount": amount}
                    for desc, amount in expenses.items()
                ]
            )

            # Create an editable dataframe with improved styling
            edited_df = st.data_editor(
                df,
                column_config={
                    "Expense": st.column_config.TextColumn(
                        "Description",
                        help="Description of the expense",
                        width="large",
                        required=True,
                    ),
                    "Amount": st.column_config.NumberColumn(
                        "Amount ($)",
                        help="Amount spent",
                        min_value=0.0,
                        format="$%.2f",
                        width="medium",
                        required=True,
                    ),
                },
                hide_index=True,
                num_rows="dynamic",
                key=f"expense_table_{category}",
                use_container_width=True,
            )

            # Check for changes and update if needed
            if not df.equals(edited_df):
                new_expenses = {
                    row["Expense"]: row["Amount"]
                    for _, row in edited_df.iterrows()
                    if pd.notna(row["Expense"]) and pd.notna(row["Amount"])
                }
                on_update(category, new_expenses)

        # Summary metrics with improved layout
        metrics_col1, metrics_col2, metrics_col3 = st.columns(3)

        with metrics_col1:
            st.metric(
                "Total Spent",
                f"${total_spent:.2f}",
                delta=(
                    f"-${budget_amount - total_spent:.2f}"
                    if total_spent > budget_amount
                    else None
                ),
                delta_color="inverse",
            )

        with metrics_col2:
            st.metric(
                "Budget",
                f"${budget_amount:.2f}",
                delta=None,
            )

        with metrics_col3:
            remaining = budget_amount - total_spent
            st.metric(
                "Remaining",
                f"${remaining:.2f}",
                delta=(
                    f"{(remaining/budget_amount)*100:.1f}%"
                    if budget_amount > 0
                    else None
                ),
                delta_color="normal" if remaining >= 0 else "inverse",
            )
