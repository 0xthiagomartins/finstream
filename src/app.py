import streamlit as st
from budget.dashboard import render_budget_dashboard
from budget.set_goals import render_budget_goals_page


def render_first_million():
    st.markdown("Financial goals and projections coming soon...")


def render_net_worth():
    st.markdown("Net worth tracking coming soon...")


# Define pages
goals_page = st.Page(render_budget_goals_page, title="Set Goals", icon="🎯")
dashboard_page = st.Page(
    render_budget_dashboard, title="Dashboard", icon="💰", default=True
)


first_million_page = st.Page(
    render_first_million,
    title="Goals & First Million",
    icon="💎",
)

net_worth_page = st.Page(
    render_net_worth,
    title="Assets vs Liabilities",
    icon="📊",
)

# Define navigation structure
pg = st.navigation(
    {
        "Budget Management": [goals_page, dashboard_page],
        "Financial Planning": [first_million_page, net_worth_page],
    }
)

# Set page configuration
st.set_page_config(
    page_title="FinStream",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://github.com/0xthiagomartins/finstream",
        "Report a bug": "https://github.com/0xthiagomartins/finstream/issues",
        "About": "# FinStream - Personal Finance Manager",
    },
)

# Set custom font and theme
st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'JetBrains Mono', monospace !important;
        }

        .stMarkdown, .stDataFrame, .stTable {
            font-family: 'JetBrains Mono', monospace !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# Run the selected page
pg.run()
