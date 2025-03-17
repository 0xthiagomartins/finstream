import streamlit as st
from budget import render_budget_dashboard, render_budget_goals_page
from first_million import render_first_million
from net_worth import render_net_worth
from crypto import render_marketcap_dashboard
from streamlit_extras.metric_cards import style_metric_cards


# Define pages
goals_page = st.Page(
    render_budget_goals_page,
    title="Set Goals",
    icon=":material/adjust:",
)

dashboard_page = st.Page(
    render_budget_dashboard,
    title="Dashboard",
    icon=":material/dashboard:",
    default=True,
)

first_million_page = st.Page(
    render_first_million,
    title="Goals & First Million",
    icon=":material/trending_up:",
)

net_worth_page = st.Page(
    render_net_worth,
    title="Net Worth",
    icon=":material/account_balance_wallet:",
)

marketcap_of_page = st.Page(
    render_marketcap_dashboard,
    title="Market Cap Of",
    icon=":material/currency_bitcoin:",
)

# Define navigation structure
pg = st.navigation(
    {
        "Budget Management": [goals_page, dashboard_page],
        "Financial Planning": [first_million_page, net_worth_page],
        "Crypto": [marketcap_of_page],
    }
)

# Set page configuration
st.set_page_config(
    page_title="FinStream",
    page_icon=":material/account_balance:",
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
style_metric_cards(
    background_color="#0E1117",
    border_color="#ce7e0000",
    border_left_color="#ce7e00",
)

# Run the selected page
pg.run()
