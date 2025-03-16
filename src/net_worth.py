import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from typing import Dict, List, Tuple
from datetime import datetime
from components.asset_liability_card import render_asset_liability_card
from utils.data_manager import save_current_state, load_saved_state

# Asset and Liability Categories
ASSET_CATEGORIES = [
    "Cash & Bank",
    "Investments",
    "Real Estate",
    "Vehicles",
    "Other Assets",
]

LIABILITY_CATEGORIES = [
    "Credit Cards",
    "Personal Loans",
    "Mortgages",
    "Vehicle Loans",
    "Other Debts",
]


def add_mock_data():
    """Add mock data for demonstration purposes."""
    # Mock Assets
    mock_assets = {
        "Cash & Bank": {
            "Checking Account": 5000.00,
            "Savings Account": 15000.00,
            "Emergency Fund": 10000.00,
        },
        "Investments": {
            "Stock Portfolio": 50000.00,
            "401(k)": 75000.00,
            "Roth IRA": 25000.00,
            "Cryptocurrency": 5000.00,
        },
        "Real Estate": {
            "Primary Residence": 350000.00,
            "Rental Property": 250000.00,
        },
        "Vehicles": {
            "Car 1": 25000.00,
            "Car 2": 15000.00,
        },
        "Other Assets": {
            "Jewelry": 5000.00,
            "Art Collection": 10000.00,
        },
    }

    # Mock Liabilities
    mock_liabilities = {
        "Credit Cards": {
            "Credit Card 1": 2500.00,
            "Credit Card 2": 1500.00,
        },
        "Personal Loans": {
            "Personal Loan": 15000.00,
            "Student Loan": 25000.00,
        },
        "Mortgages": {
            "Primary Home": 280000.00,
            "Rental Property": 200000.00,
        },
        "Vehicle Loans": {
            "Car 1 Loan": 20000.00,
            "Car 2 Loan": 10000.00,
        },
        "Other Debts": {
            "Medical Bill": 5000.00,
        },
    }

    # Add mock data to session state
    st.session_state.assets = mock_assets
    st.session_state.liabilities = mock_liabilities


def initialize_session_state():
    """Initialize session state variables."""
    if "assets" not in st.session_state:
        st.session_state.assets = {cat: {} for cat in ASSET_CATEGORIES}
    if "liabilities" not in st.session_state:
        st.session_state.liabilities = {cat: {} for cat in LIABILITY_CATEGORIES}
    if "net_worth_history" not in st.session_state:
        st.session_state.net_worth_history = []

    # Data persistence controls
    col1, col2, col3 = st.sidebar.columns(3)

    with col1:
        if st.button("Load Saved", help="Load data from CSV files"):
            load_saved_state()
            st.rerun()

    with col2:
        if st.button("Save Data", help="Save current data to CSV"):
            save_current_state()
            st.success("Data saved successfully!")

    with col3:
        if st.button("Load Demo"):
            add_mock_data()
            st.rerun()

    # Clear data button
    if st.sidebar.button("Clear All", type="secondary"):
        st.session_state.assets = {cat: {} for cat in ASSET_CATEGORIES}
        st.session_state.liabilities = {cat: {} for cat in LIABILITY_CATEGORIES}
        st.session_state.net_worth_history = []
        st.rerun()


def update_items(category: str, df: pd.DataFrame, is_asset: bool = True):
    """Update items in a category based on edited dataframe."""
    target_dict = st.session_state.assets if is_asset else st.session_state.liabilities
    target_dict[category] = {
        row["Item"]: row["Amount"]
        for _, row in df.iterrows()
        if row["Item"] and row["Amount"] > 0
    }
    # Auto-save on update
    save_current_state()


def add_item(category: str, name: str, amount: float, is_asset: bool = True):
    """Add a new item to a category."""
    target_dict = st.session_state.assets if is_asset else st.session_state.liabilities
    if category in target_dict:
        target_dict[category][name] = amount


def calculate_net_worth() -> Tuple[float, float, float]:
    """Calculate total assets, liabilities, and net worth."""
    total_assets = sum(
        sum(items.values()) for items in st.session_state.assets.values()
    )
    total_liabilities = sum(
        sum(items.values()) for items in st.session_state.liabilities.values()
    )
    net_worth = total_assets - total_liabilities
    return total_assets, total_liabilities, net_worth


def render_summary_metrics(
    total_assets: float, total_liabilities: float, net_worth: float
):
    """Render the summary metrics at the top of the dashboard."""
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Total Assets",
            f"${total_assets:,.2f}",
            help="Sum of all your assets",
        )

    with col2:
        st.metric(
            "Total Liabilities",
            f"${total_liabilities:,.2f}",
            help="Sum of all your debts",
            delta=None,
        )

    with col3:
        st.metric(
            "Net Worth",
            f"${net_worth:,.2f}",
            delta=f"${net_worth:,.2f}",
            delta_color="normal" if net_worth >= 0 else "inverse",
            help="Assets minus Liabilities",
        )


def create_distribution_chart(
    data: Dict[str, Dict[str, float]], title: str
) -> go.Figure:
    """Create a pie chart showing distribution of assets or liabilities."""
    categories = []
    values = []

    for category, items in data.items():
        if items:
            total = sum(items.values())
            categories.append(category)
            values.append(total)

    fig = go.Figure(
        data=[
            go.Pie(
                labels=categories,
                values=values,
                hole=0.4,
                textinfo="label+percent",
            )
        ]
    )

    fig.update_layout(
        title=title,
        showlegend=True,
        plot_bgcolor="#0E1117",
        paper_bgcolor="#0E1117",
        font=dict(color="#FFFFFF"),
    )

    return fig


def render_net_worth():
    """Render the net worth dashboard."""
    st.title("Net Worth Dashboard")

    # Initialize session state
    initialize_session_state()

    # Calculate current net worth
    total_assets, total_liabilities, net_worth = calculate_net_worth()

    # Display summary metrics
    render_summary_metrics(total_assets, total_liabilities, net_worth)

    # Distribution charts
    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        if any(items for items in st.session_state.assets.values()):
            fig_assets = create_distribution_chart(
                st.session_state.assets, "Asset Distribution"
            )
            st.plotly_chart(fig_assets, use_container_width=True)
        else:
            st.info("Add some assets to see their distribution")

    with col2:
        if any(items for items in st.session_state.liabilities.values()):
            fig_liabilities = create_distribution_chart(
                st.session_state.liabilities, "Liability Distribution"
            )
            st.plotly_chart(fig_liabilities, use_container_width=True)
        else:
            st.info("Add some liabilities to see their distribution")

    # Asset and Liability cards
    st.markdown("---")
    st.subheader("Edit Assets & Liabilities")
    col1, col2 = st.columns(2)
    with col1:
        for category in ASSET_CATEGORIES:
            render_asset_liability_card(
                category=category,
                items=st.session_state.assets[category],
                on_update=lambda cat, df: update_items(cat, df, True),
                on_add=lambda cat, name, amount: add_item(cat, name, amount, True),
                is_asset=True,
            )

    with col2:
        for category in LIABILITY_CATEGORIES:
            render_asset_liability_card(
                category=category,
                items=st.session_state.liabilities[category],
                on_update=lambda cat, df: update_items(cat, df, False),
                on_add=lambda cat, name, amount: add_item(cat, name, amount, False),
                is_asset=False,
            )
