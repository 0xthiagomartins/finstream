import streamlit as st
import pandas as pd
import numpy as np
from typing import List, Dict


def calculate_future_value(
    initial_amount: float,
    monthly_aport: float,
    years: int,
    annual_return: float = 0.10,  # 10% annual return by default
) -> float:
    """Calculate future value of investments."""
    months = years * 12
    monthly_rate = annual_return / 12

    # Future value formula for initial amount
    initial_fv = initial_amount * (1 + annual_return) ** years

    # Future value formula for monthly contributions
    if monthly_rate > 0:
        contribution_fv = (
            monthly_aport * ((1 + monthly_rate) ** months - 1) / monthly_rate
        )
    else:
        contribution_fv = monthly_aport * months

    return initial_fv + contribution_fv


def create_projection_table(
    initial_amount: float,
    desired_amount: float,
    aport_amounts: List[float],
    year_ranges: List[int],
) -> pd.DataFrame:
    """Create projection table for different aport amounts and time periods."""
    data = []

    for aport in aport_amounts:
        row = {"Aport Amount": f"${aport:,.2f}"}
        for years in year_ranges:
            future_value = calculate_future_value(initial_amount, aport, years)
            row[f"{years} Years"] = future_value
        data.append(row)

    df = pd.DataFrame(data)
    return df


def render_first_million():
    """Render the First Million calculator page."""
    st.title("Goals & First Million")
    st.markdown("Calculate your path to financial independence")

    # Input form
    with st.form("investment_calculator"):
        col1, col2 = st.columns(2)

        with col1:
            annual_income = st.number_input(
                "Annual Income",
                min_value=0.0,
                value=50000.0,
                step=1000.0,
                format="%.2f",
                help="Your total annual income",
            )

            initial_amount = st.number_input(
                "Initial Amount",
                min_value=0.0,
                value=0.0,
                step=1000.0,
                format="%.2f",
                help="Current investment amount",
            )

        with col2:
            monthly_income = st.number_input(
                "Monthly Income",
                min_value=0.0,
                value=annual_income / 12,
                step=100.0,
                format="%.2f",
                help="Your monthly income",
            )

            desired_amount = st.number_input(
                "Desired Amount",
                min_value=0.0,
                value=1_000_000.0,
                step=10000.0,
                format="%.2f",
                help="Your financial goal",
            )

        calculate = st.form_submit_button("Calculate Projections", type="primary")

    if calculate:
        # Define aport amounts and year ranges
        aport_amounts = [
            50.00,
            100.00,
            200.00,
            300.00,
            400.00,
            500.00,
            1000.00,
            2000.00,
            3000.00,
            5000.00,
            10000.00,
            15000.00,
            20000.00,
            30000.00,
            50000.00,
        ]

        year_ranges = [10, 15, 20, 25, 30, 35, 40]

        # Create projection table
        df = create_projection_table(
            initial_amount, desired_amount, aport_amounts, year_ranges
        )

        # Create style functions for each column
        def style_cell(val, desired_amount):
            try:
                if isinstance(val, str) and val.startswith("$"):
                    return ""
                num_val = float(val)
                return (
                    "color: #00FF00" if num_val >= desired_amount else "color: #FFFFFF"
                )
            except:
                return ""

        # Format numbers as currency and apply styling
        styled_df = df.style.apply(
            lambda x: pd.Series(
                [style_cell(val, desired_amount) for val in x], index=x.index
            ),
            axis=1,
        )

        # Format values as currency
        for col in df.columns:
            if col != "Aport Amount":
                styled_df = styled_df.format({col: "${:,.2f}"})

        # Display styled table
        st.dataframe(
            styled_df,
            column_config={
                "Aport Amount": st.column_config.TextColumn(
                    "Monthly Investment",
                    help="Monthly investment amount",
                ),
                **{
                    f"{year} Years": st.column_config.TextColumn(
                        f"{year} Years",
                        help=f"Projected value after {year} years",
                    )
                    for year in year_ranges
                },
            },
            hide_index=True,
            use_container_width=True,
        )

        # Add explanatory text
        st.markdown(
            """
        ### Assumptions:
        - Annual return rate: 10%
        - Calculations consider compound interest
        - Values in green indicate reaching your desired amount
        - All projections include your initial investment amount
        """
        )
