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
    
    # Description
    st.markdown("""
    Calculate how your investments can grow over time with compound interest.
    Compound interest is calculated on the initial principal and also on the accumulated 
    interest of previous periods.
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