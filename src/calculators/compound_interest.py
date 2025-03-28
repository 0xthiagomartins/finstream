import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

def calculate_compound_interest(
    initial_amount: float,
    interest_rate: float,
    period: int,
    monthly_investment: float,
    is_rate_annual: bool = True,
    is_period_annual: bool = False
) -> pd.DataFrame:
    """
    Calculate compound interest over time.
    
    Args:
        initial_amount: Initial investment amount
        interest_rate: Interest rate (annual or monthly based on is_rate_annual)
        period: Investment period (in years or months based on is_period_annual)
        monthly_investment: Monthly contribution amount
        is_rate_annual: Whether interest_rate is annual (True) or monthly (False)
        is_period_annual: Whether period is in years (True) or months (False)
    """
    # Convert annual rate to monthly if needed
    monthly_rate = interest_rate / 12 if is_rate_annual else interest_rate
    
    # Convert period to months if needed
    total_months = period * 12 if is_period_annual else period
    
    # Initialize arrays for tracking values
    months = range(1, total_months + 1)
    invested_amounts = []
    interest_amounts = []
    total_amounts = []
    
    current_amount = initial_amount
    total_invested = initial_amount
    
    for month in months:
        # Add monthly investment
        current_amount += monthly_investment
        total_invested += monthly_investment
        
        # Calculate interest
        interest = current_amount * monthly_rate
        current_amount += interest
        
        # Store values
        invested_amounts.append(total_invested)
        total_amounts.append(current_amount)
        interest_amounts.append(current_amount - total_invested)
    
    # Create DataFrame
    df = pd.DataFrame({
        'Month': months,
        'Total Invested': invested_amounts,
        'Interest': interest_amounts,
        'Total Amount': total_amounts
    })
    
    return df

def render_compound_calculator():
    """Render the compound interest calculator interface."""
    st.title("Compound Interest Calculator")
    
    # Add detailed explanation in an expander
    with st.expander("What is Compound Interest?", expanded=False):
        st.markdown("""
        ### What is Compound Interest?
        
        Compound interest is interest calculated not only on the initial principal but also on the accumulated interest over time, resulting in the famous "interest on interest" effect.
        
        As interest is added to the initial capital, the total amount increases, and subsequent interest is calculated based on this new value.
        
        In practice, this generates an exponential growth effect, which is highly beneficial for long-term investors (receiving interest on interest) but can be detrimental for those taking long-term loans and financing (paying interest on interest).
        
        ### How Does the Compound Interest Formula Work?
        
        The compound interest formula is:
        
        **M = P(1+r)^t**
        
        Where:
        - M is the total amount, including principal and accumulated interest
        - P is the principal (initial investment or loan amount)
        - r is the interest rate per period
        - t is the time period over which interest is applied
        
        ### Practical Example
        
        Let's say you make an initial investment of $10,000 with a 10% annual interest rate. Let's calculate the amount after 3 years:
        
        - P = $10,000 (initial capital)
        - r = 10% (annual interest rate)
        - t = 3 years (time)
        
        Plugging these values into the formula:
        M = 10,000 * (1 + 0.10)^3
        
        Calculating (1 + 0.10)^3:
        (1 + 0.10)^3 = 1.10 * 1.10 * 1.10 = 1.331
        
        Multiplying the initial capital by the result:
        M = 10,000 * 1.331 = $13,310
        
        Therefore, after 3 years, with a 10% annual interest rate and an initial investment of $10,000, the total amount would be $13,310.
        
        Fun fact: Under the same conditions with simple interest, the final amount would be $13,000.
        
        ### Simple vs. Compound Interest
        
        The difference between simple and compound interest lies in how interest is calculated over time:
        - Simple interest is calculated only on the initial amount
        - Compound interest is calculated on both the initial amount and previously accumulated interest
        
        In terms of results, compound interest tends to accumulate a larger amount over time than simple interest.
        
        ### Benefits for Investors
        
        Compound interest offers several benefits to investors, but the main advantage is the potential for accelerated investment growth over time.
        
        As interest and dividends are reinvested, the total amount increases exponentially, allowing investors to grow their wealth more rapidly.
        
        ### Strategies to Maximize Compound Interest
        
        To make the most of compound interest, consider these strategies:
        
        1. Start investing as early as possible to maximize growth time
        2. Maintain investments for long periods to allow continuous compound interest accumulation
        3. Make regular monthly contributions to your investments
        4. Look for investment options with competitive interest rates
        5. Reinvest earnings to increase principal and boost compound interest growth
        
        To enhance the compound interest effect, investors typically make regular monthly contributions, which this calculator helps you simulate.
        """)
    
    # Input form
    with st.form("compound_calculator"):
        col1, col2 = st.columns(2)
        
        with col1:
            initial_amount = st.number_input(
                "Initial Amount ($)",
                min_value=0.0,
                value=1000.0,
                step=100.0,
                help="Initial investment amount"
            )
            
            interest_rate = st.number_input(
                "Interest Rate (%)",
                min_value=0.0,
                max_value=100.0,
                value=10.0,
                step=0.1,
                help="Annual interest rate percentage"
            )
            
            is_rate_annual = st.toggle(
                "Annual Rate",
                value=True,
                help="Toggle between annual and monthly interest rate"
            )
        
        with col2:
            period = st.number_input(
                "Investment Period",
                min_value=1,
                value=5,
                step=1,
                help="Investment time period"
            )
            
            is_period_annual = st.toggle(
                "Period in Years",
                value=True,
                help="Toggle between years and months"
            )
            
            monthly_investment = st.number_input(
                "Monthly Investment ($)",
                min_value=0.0,
                value=100.0,
                step=50.0,
                help="Additional monthly investment amount"
            )
        
        calculate = st.form_submit_button("Calculate", type="primary")
    
    if calculate:
        # Calculate results
        df = calculate_compound_interest(
            initial_amount,
            interest_rate / 100,  # Convert percentage to decimal
            period,
            monthly_investment,
            is_rate_annual,
            is_period_annual
        )
        
        # Display summary
        final_row = df.iloc[-1]
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Total Amount",
                f"${final_row['Total Amount']:,.2f}",
                help="Final investment value including interest"
            )
        
        with col2:
            st.metric(
                "Total Invested",
                f"${final_row['Total Invested']:,.2f}",
                help="Total amount invested (initial + monthly contributions)"
            )
        
        with col3:
            st.metric(
                "Total Interest",
                f"${final_row['Interest']:,.2f}",
                help="Total interest earned"
            )
        
        # Create donut chart
        fig1 = go.Figure(data=[go.Pie(
            labels=['Total Invested', 'Interest Earned'],
            values=[final_row['Total Invested'], final_row['Interest']],
            hole=.7,
            marker_colors=['#1f77b4', '#2ca02c']
        )])
        
        fig1.update_layout(
            title="Investment Breakdown",
            showlegend=True,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        # Create stacked bar chart
        fig2 = go.Figure(data=[
            go.Bar(
                name='Interest',
                x=df['Month'],
                y=df['Interest'],
                marker_color='#2ca02c'
            ),
            go.Bar(
                name='Invested Amount',
                x=df['Month'],
                y=df['Total Invested'],
                marker_color='#1f77b4'
            )
        ])
        
        fig2.update_layout(
            barmode='stack',
            title='Investment Growth Over Time',
            xaxis_title='Month',
            yaxis_title='Amount ($)',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        # Display charts
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(fig1, use_container_width=True)
        with col2:
            st.plotly_chart(fig2, use_container_width=True)
        
        # Display detailed table
        st.subheader("Detailed Breakdown")
        st.dataframe(
            df.style.format({
                'Total Invested': '${:,.2f}',
                'Interest': '${:,.2f}',
                'Total Amount': '${:,.2f}'
            }),
            hide_index=True,
            use_container_width=True
        ) 