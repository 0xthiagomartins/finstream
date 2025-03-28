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


def calculate_time_to_goal(initial_amount: float, monthly_investment: float, annual_return: float, goal_amount: float) -> tuple:
    """Calculate time needed to reach financial goal with given monthly investment."""
    monthly_rate = annual_return / 12
    total_months = 0
    current_amount = initial_amount
    
    while current_amount < goal_amount:
        current_amount += monthly_investment
        interest = current_amount * monthly_rate
        current_amount += interest
        total_months += 1
        
        if total_months > 1200:  # 100 years limit
            return None
    
    years = total_months // 12
    months = total_months % 12
    total_invested = initial_amount + (monthly_investment * total_months)
    total_interest = current_amount - total_invested
    
    return years, months, current_amount, total_invested, total_interest


def calculate_required_monthly_investment(initial_amount: float, years: int, annual_return: float, goal_amount: float) -> tuple:
    """Calculate required monthly investment to reach goal in given time."""
    months = years * 12
    monthly_rate = annual_return / 12
    
    future_value_initial = initial_amount * (1 + annual_return) ** years
    remaining_value = goal_amount - future_value_initial
    
    if monthly_rate > 0:
        monthly_payment = (remaining_value * monthly_rate) / ((1 + monthly_rate) ** months - 1)
    else:
        monthly_payment = remaining_value / months
    
    # Calculate final values
    current_amount = initial_amount
    for _ in range(months):
        current_amount += monthly_payment
        interest = current_amount * monthly_rate
        current_amount += interest
    
    total_invested = initial_amount + (monthly_payment * months)
    total_interest = current_amount - total_invested
    
    return monthly_payment, current_amount, total_invested, total_interest


def create_investment_timeline(initial_amount: float, monthly_investment: float, years: int, annual_return: float) -> pd.DataFrame:
    """Create a DataFrame with monthly investment data."""
    monthly_rate = annual_return / 12
    data = []
    current_amount = initial_amount
    
    # Initialize first month
    data.append({
        'Month': 0,
        'Total Amount': initial_amount,
        'Total Invested': initial_amount,
        'Total Returns': 0,
        'Monthly Return': 0
    })
    
    # Calculate monthly data
    for month in range(1, (years * 12) + 1):
        current_amount += monthly_investment
        interest = current_amount * monthly_rate
        current_amount += interest
        
        total_invested = initial_amount + (monthly_investment * month)
        total_returns = current_amount - total_invested
        monthly_return = interest
        
        data.append({
            'Month': month,
            'Total Amount': current_amount,
            'Total Invested': total_invested,
            'Total Returns': total_returns,
            'Monthly Return': monthly_return
        })
    
    return pd.DataFrame(data)


def render_investment_visualizations(timeline_df: pd.DataFrame, goal_amount: float):
    """Render investment visualizations using plotly."""
    final_row = timeline_df.iloc[-1]
    
    # Create two columns for the charts
    col1, col2 = st.columns([1, 2])  # Adjusted ratio for better visibility
    
    with col1:
        # 1. Donut chart for final composition
        fig_donut = go.Figure(data=[go.Pie(
            labels=['Total Invested', 'Total Returns'],
            values=[final_row['Total Invested'], final_row['Total Returns']],
            hole=.6,
            marker_colors=['#1f77b4', '#ce7e00']
        )])
        fig_donut.update_layout(
            title='Final Investment Composition',
            showlegend=True,
            height=400,
            annotations=[dict(
                text=f'${final_row["Total Amount"]:,.0f}',
                x=0.5,
                y=0.5,
                font_size=20,
                showarrow=False
            )]
        )
        st.plotly_chart(fig_donut, use_container_width=True)
    
    with col2:
        # 2. Monthly stacked bar chart
        fig_bar = go.Figure()
        
        # Add invested amount bars
        fig_bar.add_trace(go.Bar(
            name='Invested Amount',
            x=timeline_df['Month'],
            y=timeline_df['Total Invested'],
            marker_color='#1f77b4'
        ))
        
        # Add returns bars
        fig_bar.add_trace(go.Bar(
            name='Returns',
            x=timeline_df['Month'],
            y=timeline_df['Total Returns'],
            marker_color='#ce7e00'
        ))
        
        # Update layout
        fig_bar.update_layout(
            title='Monthly Investment Growth',
            barmode='stack',
            height=400,
            showlegend=True,
            xaxis_title='Month',
            yaxis_title='Amount ($)',
            hovermode='x unified',
            # Add hover template
            hoverlabel=dict(
                bgcolor="white",
                font_size=16,
            )
        )
        
        # Add goal amount line
        fig_bar.add_trace(go.Scatter(
            x=timeline_df['Month'],
            y=[goal_amount] * len(timeline_df),
            name='Goal Amount',
            line=dict(color='red', width=2, dash='dash')
        ))
        
        # Update traces for better hover information
        fig_bar.update_traces(
            hovertemplate="<br>".join([
                "Month: %{x}",
                "Amount: $%{y:,.2f}",
                "<extra></extra>"
            ])
        )
        
        st.plotly_chart(fig_bar, use_container_width=True)
    
    
    # 4. Detailed table (now showing monthly data)
    st.markdown("### Detailed Monthly Breakdown")
    display_df = timeline_df.copy()
    # Convert month numbers to more readable format
    display_df['Month'] = display_df['Month'].apply(lambda x: f"Month {x}")
    
    st.dataframe(
        display_df.style.format({
            'Total Amount': '${:,.2f}',
            'Total Invested': '${:,.2f}',
            'Total Returns': '${:,.2f}',
            'Monthly Return': '${:,.2f}'
        }),
        hide_index=True,
        use_container_width=True
    )


def render_first_million():
    """Render the financial goal calculator page."""
    st.title("Financial Goal Calculator")
    
    # Detailed description in an expander
    with st.expander("About the Financial Goal Calculator", expanded=False):
        st.markdown("""
        ### What is the Financial Goal Calculator?
        
        The dream of reaching significant financial milestones is something many individuals share. Whether it's to ensure financial security, fulfill dreams, or achieve economic freedom, these milestones represent important steps toward personal achievement.
        
        The good news is that reaching your financial goals doesn't have to be a mystery. With the help of this Financial Goal Calculator, you can create a clear and realistic plan to get there.
        
        ### How Does the Calculator Work?
        
        This Financial Goal Calculator is a powerful tool designed to simplify the financial planning process. It offers an approach to estimate how much money you would need to invest monthly to reach your financial goal within a specific period, considering a particular interest rate.
        
        #### How to Use:
        1. **Enter Your Initial Information**: Start by entering the value you currently have invested. This includes any savings or investments you've already accumulated.
        2. **Set the Interest Rate**: Choose the interest rate you expect to earn on your investments over time. This can vary depending on the type of investment and economic conditions.
        3. **Choose the Investment Period**: Determine the number of years in which you want to reach your financial goal. This can be adapted according to your personal financial goals.
        
        The calculator will then automatically provide the monthly amount you should invest to reach your goal within the chosen timeframe, based on the selected interest rate.
        
        ### The Formula
        
        The formula used to calculate the estimated monthly investment value is:
        
        **PMT = (FV − PV) * r / ((1+r)^n −1)**
        
        Where:
        - PMT is the monthly payment (the amount you need to invest every month)
        - FV is the desired future value (your financial goal)
        - r is the monthly interest rate (annual interest rate divided by 12 months)
        - n is the total number of months
        
        ### Tips for Reaching Your Financial Goals
        
        Investing consistently and intelligently is key to reaching your financial goals. Here are some tips that can help:
        
        1. **Diversify Your Investments**: Don't put all your eggs in one basket. Diversifying your investments reduces risk and increases the chances of consistent returns over time.
        
        2. **Maintain Discipline**: Commit to investing regularly, even when the market goes through ups and downs. Discipline is essential for long-term success.
        
        3. **Harness the Power of Compound Interest**: The earlier you start investing, the more time your investments have to grow with compound interest. Start as soon as possible!
        
        4. **Educate Yourself Financially**: Invest time in learning about different types of investments, strategies, and financial concepts. The more you know, the better your decisions will be.
        
        Remember that patience, consistency, and knowledge are your allies on this journey toward financial independence.
        
        ### Example Calculation
        
        Let's say you have an initial investment of $10,000, a monthly interest rate of 0.5% (or 6% annually), and want to reach $1 million in 20 years:
        
        - Initial Value (PV) = $10,000
        - Goal Amount (FV) = $1,000,000
        - Monthly Rate (r) = 0.005
        - Time Period (n) = 20 years * 12 = 240 months
        
        Using the formula above, you would need to invest approximately $2,134.64 monthly to reach your goal.
        
        Note that this is just an example for illustration purposes. Your circumstances and financial goals may vary, so it's important to enter your own values in the calculator to get personalized estimates.
        """)
    
    # Calculator mode toggle
    calc_mode = st.toggle(
        "Calculate Required Monthly Investment",
        help="Toggle between calculating time needed or required monthly investment"
    )
    
    # Input form
    with st.form("goal_calculator"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            initial_amount = st.number_input(
                "Current Savings ($)",
                min_value=0.0,
                value=100_000.0,
                step=1000.0,
                help="How much you currently have saved and invested"
            )
            
            goal_amount = st.number_input(
                "Goal Amount ($)",
                min_value=100_000.0,
                value=1_000_000.0,
                step=100_000.0,
                help="Your desired financial goal"
            )
        
        with col2:
            annual_return = st.number_input(
                "Annual Return Rate (%)",
                min_value=0.0,
                max_value=100.0,
                value=10.0,
                step=0.1,
                help="Expected annual return rate"
            )
        
        with col3:
            if calc_mode:
                # Monthly Investment Required mode
                investment_years = st.number_input(
                    "Years to Reach Goal",
                    min_value=1,
                    value=10,
                    step=1,
                    help="In how many years do you want to reach your goal"
                )
            else:
                # Time to Goal mode
                monthly_investment = st.number_input(
                    "Monthly Investment ($)",
                    min_value=0.0,
                    value=3000.0,
                    step=100.0,
                    help="How much you can invest monthly"
                )
        
        calculate = st.form_submit_button("Calculate", type="primary")
    
    if calculate:
        if calc_mode:
            # Calculate required monthly investment
            monthly_needed, final_amount, total_invested, total_interest = calculate_required_monthly_investment(
                initial_amount, investment_years, annual_return / 100, goal_amount
            )
            
            # Display summary
            st.markdown(
                f"""
                ### Required Monthly Investment
                
                Considering your initial ${initial_amount:,.2f} in savings and investments, 
                you need to invest **${monthly_needed:,.2f} monthly** to reach ${goal_amount:,.2f} in {investment_years} years!
                
                This way, you will reach ${final_amount:,.2f}, with ${total_invested:,.2f} invested 
                and ${total_interest:,.2f} in returns.
                """
            )
            
            # Display metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Final Amount", f"${final_amount:,.2f}")
            with col2:
                st.metric("Total Invested", f"${total_invested:,.2f}")
            with col3:
                st.metric("Total Returns", f"${total_interest:,.2f}")
            with col4:
                st.metric("Required Monthly Investment", f"${monthly_needed:,.2f}")
            
            # Add visualizations
            timeline_df = create_investment_timeline(
                initial_amount,
                monthly_needed,
                investment_years,
                annual_return / 100
            )
            render_investment_visualizations(timeline_df, goal_amount)
            
        else:
            # Calculate time needed
            result = calculate_time_to_goal(
                initial_amount, monthly_investment, annual_return / 100, goal_amount
            )
            
            if result:
                years, months, final_amount, total_invested, total_interest = result
                
                # Display summary
                st.markdown(
                    f"""
                    ### Investment Timeline
                    
                    You will reach ${goal_amount:,.2f} in **{years} years and {months} months**.
                    
                    After this period, the total amount will be {final_amount:,.2f}, 
                    with {total_invested:,.2f} invested and {total_interest:,.2f} in returns.
                    """
                )
                
                # Display metrics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Final Amount", f"${final_amount:,.2f}")
                with col2:
                    st.metric("Total Invested", f"${total_invested:,.2f}")
                with col3:
                    st.metric("Total Returns", f"${total_interest:,.2f}")
                with col4:
                    st.metric(
                        "Time to Goal", 
                        f"{years}y {months}m"
                    )
                
                # Add visualizations
                timeline_df = create_investment_timeline(
                    initial_amount,
                    monthly_investment,
                    years + (1 if months > 0 else 0),
                    annual_return / 100
                )
                render_investment_visualizations(timeline_df, goal_amount)
            else:
                st.error(
                    "With the current parameters, it will take over 100 years to reach your goal. "
                    "Consider increasing your monthly investment or expected return rate."
                )
        
        # Continue with existing visualization code...
