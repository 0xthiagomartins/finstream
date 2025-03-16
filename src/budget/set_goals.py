import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from models.budget_goal import BudgetGoal
import pandas as pd
from utils.data_manager import save_budget_state, load_budget_state
from typing import Dict


def load_demo_goals():
    """Load demo budget goals data."""
    # Demo budget allocations
    demo_allocations = {
        "Housing": 30.0,  # Common rule of thumb for housing
        "Food": 15.0,  # Essential expense
        "Transportation": 10.0,
        "Utilities": 10.0,
        "Entertainment": 5.0,
        "Investment": 20.0,  # Savings/investment
        "Travel": 5.0,
        "Education": 5.0,
    }

    # Set budget goals
    try:
        st.session_state.budget_goal = BudgetGoal(demo_allocations)
        st.session_state.budget_goals = demo_allocations
        save_budget_state(
            demo_allocations,
            st.session_state.expenses,
            st.session_state.monthly_salary,
        )
        st.success("Demo goals loaded successfully!")
    except ValueError as e:
        st.error(f"Error setting demo budget goals: {str(e)}")
        st.session_state.budget_goal = None


def save_budget_goals(allocations: Dict[str, float]):
    """Save budget goals and create BudgetGoal object."""
    try:
        budget_goal = BudgetGoal(allocations)
        st.session_state.budget_goal = budget_goal
        st.session_state.budget_goals = allocations
        save_budget_state(
            allocations, st.session_state.expenses, st.session_state.monthly_salary
        )
        return True
    except ValueError as e:
        st.error(str(e))
        return False


def render_budget_goals_page():
    """Render the budget goals page."""
    st.title("Budget Goals")

    # Data persistence controls
    col1, col2, col3 = st.sidebar.columns(3)

    with col1:
        if st.button("Load Saved", help="Load data from CSV files"):
            load_budget_state()
            st.rerun()

    with col2:
        if st.button("Save Data", help="Save current data to CSV"):
            if st.session_state.budget_goals:
                save_budget_state(
                    st.session_state.budget_goals,
                    st.session_state.expenses,
                    st.session_state.monthly_salary,
                )
                st.success("Data saved successfully!")
            else:
                st.warning("Please set budget goals before saving")

    with col3:
        if st.button("Load Demo", help="Load demo goals"):
            load_demo_goals()
            st.rerun()

    if "categories" not in st.session_state:
        st.error("Categories not initialized. Please visit the Budget Dashboard first.")
        return

    # Add description
    st.markdown(
        """
        Set your budget allocation goals by adjusting the sliders below. 
        The total allocation must equal 100%.
        """
    )

    # Create main columns for layout
    col1, col2 = st.columns([1.5, 1])

    # Column 2: Sliders and Controls
    with col2:
        st.markdown("### Allocations")
        allocations = {}
        remaining = 100.0

        # Create a DataFrame for current allocations
        current_allocations = pd.DataFrame(
            {
                "Category": st.session_state.categories["expense"],
                "Current": [
                    float(
                        st.session_state.budget_goal.allocations.get(category, 0.0)
                        if st.session_state.budget_goal
                        else 0.0
                    )
                    for category in st.session_state.categories["expense"]
                ],
            }
        )

        # Display allocations in a data editor
        edited_df = st.data_editor(
            current_allocations,
            column_config={
                "Category": st.column_config.TextColumn(
                    "Category",
                    help="Budget category",
                    width="medium",
                    disabled=True,
                ),
                "Current": st.column_config.NumberColumn(
                    "Allocation %",
                    help="Percentage of budget to allocate",
                    min_value=0.0,
                    max_value=100.0,
                    step=1.0,
                    format="%.1f%%",
                ),
            },
            hide_index=True,
            use_container_width=True,
        )

        # Calculate remaining allocation
        total_allocation = edited_df["Current"].sum()
        remaining = 100.0 - total_allocation

        # Show remaining allocation with color coding
        if remaining > 0:
            st.info(f"Remaining allocation: {remaining:.1f}%")
        elif remaining < 0:
            st.error(f"Over-allocated by: {-remaining:.1f}%")
        else:
            st.success("Perfect allocation: 100%")

        # Save button handling
        if st.button(
            "Save Budget Goals",
            disabled=abs(remaining) > 0.01,  # Allow small floating point differences
            type="primary",
            use_container_width=True,
        ):
            allocations = {
                row["Category"]: row["Current"]
                for _, row in edited_df.iterrows()
                if row["Current"] > 0
            }
            if save_budget_goals(allocations):
                st.success("Budget goals saved successfully!")
                st.rerun()

    # Column 1: Visualization
    with col1:
        st.markdown("### Budget Distribution")

        # Get current allocations from the edited DataFrame
        current_allocations = {
            row["Category"]: row["Current"]
            for _, row in edited_df.iterrows()
            if row["Current"] > 0
        }

        # Show visualization if we have allocations
        if current_allocations:
            total = sum(current_allocations.values())
            if abs(100 - total) <= 0.01:  # Check if total is approximately 100%
                fig = go.Figure(
                    data=[
                        go.Pie(
                            values=list(current_allocations.values()),
                            labels=list(current_allocations.keys()),
                            hole=0.6,
                            textinfo="label+percent",
                            marker_colors=px.colors.qualitative.Set3,
                        )
                    ]
                )
                fig.update_layout(
                    showlegend=False,
                    height=500,
                    annotations=[
                        dict(
                            text=f"{total:.1f}%<br>Allocated",
                            x=0.5,
                            y=0.5,
                            font_size=16,
                            showarrow=False,
                        )
                    ],
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Total allocation must equal 100% to visualize")
        else:
            st.info("Set your budget goals using the editor")


def main():
    render_budget_goals_page()


def update_goals(goals: dict):
    """Update budget goals and save to CSV."""
    st.session_state.budget_goals = goals
    save_budget_state()
