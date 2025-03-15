import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from models.budget_goal import BudgetGoal
import pandas as pd


def render_budget_goals_page():
    """Render the budget goals page."""
    st.title("Budget Goals")

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

        # Convert edited values to allocations dict
        allocations = {
            row["Category"]: row["Current"]
            for _, row in edited_df.iterrows()
            if row["Current"] > 0
        }

        # Save button
        if st.button(
            "Save Budget Goals",
            disabled=abs(remaining) > 0.01,  # Allow small floating point differences
            type="primary",
            use_container_width=True,
        ):
            try:
                st.session_state.budget_goal = BudgetGoal(allocations)
                st.success("Budget goals saved successfully!")
                st.rerun()
            except ValueError as e:
                st.error(str(e))

    # Column 1: Visualization
    with col1:
        st.markdown("### Budget Distribution")
        if allocations:
            # Show current allocations even if not saved
            total = sum(allocations.values())
            if abs(100 - total) <= 0.01:  # Check if total is approximately 100%
                fig = go.Figure(
                    data=[
                        go.Pie(
                            values=list(allocations.values()),
                            labels=list(allocations.keys()),
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

                # Add a table showing monthly amounts based on salary
                if st.session_state.monthly_salary > 0:
                    st.markdown("### Monthly Breakdown")
                    monthly_data = [
                        {
                            "Category": cat,
                            "Percentage": f"{pct:.1f}%",
                            "Monthly Amount": f"${st.session_state.monthly_salary * (pct/100):.2f}",
                        }
                        for cat, pct in allocations.items()
                    ]
                    st.dataframe(
                        pd.DataFrame(monthly_data),
                        column_config={
                            "Category": st.column_config.TextColumn(
                                "Category",
                                help="Budget category",
                                width="medium",
                            ),
                            "Percentage": st.column_config.TextColumn(
                                "Allocation",
                                help="Percentage of total budget",
                                width="small",
                            ),
                            "Monthly Amount": st.column_config.TextColumn(
                                "Monthly Amount",
                                help="Dollar amount based on monthly salary",
                                width="medium",
                            ),
                        },
                        hide_index=True,
                        use_container_width=True,
                    )
            else:
                st.warning(
                    f"Total allocation ({total:.1f}%) must equal 100% to visualize"
                )
        else:
            st.info("Set your budget goals using the editor")


def main():
    render_budget_goals_page()
