import streamlit as st
import pandas as pd
import numpy as np
from typing import List, Dict
from math import ceil
import plotly.graph_objects as go
from utils.data_manager import save_current_state, load_saved_state


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


def calculate_minimum_aport(
    initial_amount: float,
    desired_amount: float,
    years: int,
    annual_return: float = 0.10,
) -> float:
    """Calculate minimum monthly aport needed to reach desired amount in given years."""
    months = years * 12
    monthly_rate = annual_return / 12

    # Rearrange future value formula to solve for monthly payment
    # FV = P(1+r)^n + PMT*[((1+r)^n - 1)/r]
    # where FV = desired_amount, P = initial_amount, r = monthly_rate, n = months, PMT = monthly payment

    future_value_initial = initial_amount * (1 + annual_return) ** years
    remaining_value = desired_amount - future_value_initial

    if monthly_rate > 0:
        monthly_payment = (remaining_value * monthly_rate) / (
            (1 + monthly_rate) ** months - 1
        )
    else:
        monthly_payment = remaining_value / months

    # Round up to nearest 100
    return ceil(monthly_payment / 100) * 100


def create_aport_amounts(
    annual_income: float, min_aport: float, qtd: int = 10
) -> List[float]:
    """Create list of 10 aport amounts based on annual income and minimum required aport."""
    monthly_income = annual_income / 12

    # Start with 1% of monthly income, rounded to nearest 100
    base_aport = ceil((monthly_income * 0.01) / 100) * 100

    # Create geometric progression between base_aport and min_aport
    if min_aport <= base_aport:
        # If min_aport is less than base_aport, use arithmetic progression
        step = (min_aport - base_aport) / (qtd - 1)
        return [round(base_aport + step * i, 2) for i in range(qtd)]
    else:
        # If min_aport is greater than base_aport, use geometric progression
        ratio = (min_aport / base_aport) ** (1 / (qtd - 1))
        return [round(base_aport * (ratio**i), 2) for i in range(qtd)]


def calculate_year_ranges(
    initial_amount: float,
    desired_amount: float,
    monthly_income: float,
    annual_return: float = 0.10,
    min_years: int = 5,
    max_years: int = 40,
    num_points: int = 7,
) -> List[int]:
    """Calculate appropriate year ranges based on user inputs."""
    # Calculate minimum years needed with maximum reasonable investment (50% of monthly income)
    max_monthly_investment = monthly_income * 0.5

    # Find minimum years needed using binary search
    min_years_needed = min_years
    max_years_needed = max_years

    while min_years_needed < max_years_needed:
        mid_years = (min_years_needed + max_years_needed) // 2
        future_value = calculate_future_value(
            initial_amount, max_monthly_investment, mid_years, annual_return
        )

        if future_value >= desired_amount:
            max_years_needed = mid_years
        else:
            min_years_needed = mid_years + 1

    # Calculate optimal year ranges
    min_range = max(min_years, min_years_needed - 5)
    max_range = min(max_years, min_years_needed + 20)

    # Create evenly spaced year points
    step = max((max_range - min_range) // (num_points - 1), 1)
    year_ranges = list(range(min_range, max_range + 1, step))

    # Ensure we have exactly num_points
    while len(year_ranges) > num_points:
        # Remove points from the middle to maintain start and end
        idx = len(year_ranges) // 2
        year_ranges.pop(idx)

    while len(year_ranges) < num_points:
        # Add points in the largest gaps
        gaps = [
            (year_ranges[i + 1] - year_ranges[i], i)
            for i in range(len(year_ranges) - 1)
        ]
        max_gap, idx = max(gaps)
        new_year = year_ranges[idx] + max_gap // 2
        year_ranges.insert(idx + 1, new_year)

    return sorted(year_ranges)


def save_first_million_inputs(
    initial_amount: float,
    desired_amount: float,
    annual_income: float,
    monthly_income: float,
):
    """Save first million calculator inputs."""
    st.session_state.first_million_config = {
        "initial_amount": initial_amount,
        "desired_amount": desired_amount,
        "annual_income": annual_income,
        "monthly_income": monthly_income,
    }
    save_current_state()


def render_first_million():
    """Render the First Million calculator page."""
    st.title("Goals & First Million")
    st.markdown("Calculate your path to financial independence")

    # Data persistence controls
    col1, col2 = st.sidebar.columns(2)

    with col1:
        if st.button("Load Saved", help="Load data from CSV files"):
            load_saved_state()
            if "first_million_config" in st.session_state:
                config = st.session_state.first_million_config
                st.session_state.annual_income = config.get("annual_income", 100_000.0)
                st.session_state.monthly_income = config.get(
                    "monthly_income", st.session_state.annual_income / 12
                )
            st.rerun()

    with col2:
        if st.button("Save Data", help="Save current data to CSV"):
            save_current_state()
            st.success("Data saved successfully!")

    # Initialize session state for income values if not exists
    if "annual_income" not in st.session_state:
        st.session_state.annual_income = 100_000.0
    if "monthly_income" not in st.session_state:
        st.session_state.monthly_income = st.session_state.annual_income / 12

    # Income inputs outside the form
    col1, col2 = st.columns(2)

    with col1:
        if (
            st.number_input(
                "Annual Income",
                min_value=0.0,
                value=st.session_state.annual_income,
                step=1000.0,
                format="%.2f",
                help="Your total annual income",
                key="annual_income_input",
            )
            != st.session_state.annual_income
        ):
            st.session_state.annual_income = st.session_state.annual_income_input
            st.session_state.monthly_income = st.session_state.annual_income / 12
            st.rerun()

    with col2:
        if (
            st.number_input(
                "Monthly Income",
                min_value=0.0,
                value=st.session_state.monthly_income,
                step=100.0,
                format="%.2f",
                help="Your monthly income",
                key="monthly_income_input",
            )
            != st.session_state.monthly_income
        ):
            st.session_state.monthly_income = st.session_state.monthly_income_input
            st.session_state.annual_income = st.session_state.monthly_income * 12
            st.rerun()

    # Form for other inputs and calculations
    with st.form("investment_calculator"):
        col1, col2 = st.columns(2)

        with col1:
            initial_amount = st.number_input(
                "Initial Amount",
                min_value=0.0,
                value=100_000.0,
                step=1000.0,
                format="%.2f",
                help="Current investment amount",
            )

        with col2:
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
        save_first_million_inputs(
            initial_amount,
            desired_amount,
            st.session_state.annual_income,
            st.session_state.monthly_income,
        )

        # Calculate dynamic year ranges
        year_ranges = calculate_year_ranges(
            initial_amount=initial_amount,
            desired_amount=desired_amount,
            monthly_income=st.session_state.monthly_income,
            min_years=5,
            max_years=40,
            num_points=7,
        )

        # Calculate minimum aport needed for first year in range
        min_aport = calculate_minimum_aport(
            initial_amount=initial_amount,
            desired_amount=desired_amount,
            years=year_ranges[0],
        )

        # Create aport amounts based on annual income and minimum required
        aport_amounts = create_aport_amounts(
            annual_income=st.session_state.annual_income,
            min_aport=min_aport,
            qtd=15,
        )

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

        # Create accumulation plot
        fig = go.Figure()

        # Create detailed year range for plot (year by year)
        plot_years = list(range(1, max(year_ranges) + 1))

        # Add a line for each aport amount
        for aport in aport_amounts:
            y_values = [
                calculate_future_value(initial_amount, aport, year)
                for year in plot_years
            ]

            fig.add_trace(
                go.Scatter(
                    x=plot_years,
                    y=y_values,
                    name=f"${aport:,.2f}/month",
                    hovertemplate="Year %{x}<br>Amount: $%{y:,.2f}<extra></extra>",
                )
            )

        # Add horizontal line for desired amount
        fig.add_hline(
            y=desired_amount,
            line_dash="dash",
            line_color="#ce7e00",
            annotation_text="Goal",
            annotation_position="right",
        )

        # Update layout
        fig.update_layout(
            title="Investment Growth Projection",
            xaxis_title="Years",
            yaxis_title="Accumulated Amount ($)",
            hovermode="x unified",
            showlegend=True,
            legend_title="Monthly Investment",
            plot_bgcolor="#0E1117",
            paper_bgcolor="#0E1117",
            font=dict(color="#FFFFFF"),
            xaxis=dict(
                gridcolor="#2e3026",
                tickformat="d",
                # Add tick for each year
                dtick=1,
            ),
            yaxis=dict(
                gridcolor="#2e3026",
                tickformat="$,.0f",
                range=[
                    0,
                    min(
                        desired_amount * 1.5,  # Maximum 5x the goal
                        max(
                            desired_amount * 1.5,  # Minimum +20% of goal
                            max(
                                y_values
                            ),  # But never less than maximum projected value
                        ),
                    ),
                ],
            ),
        )

        # Display plot
        st.plotly_chart(fig, use_container_width=True)

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
