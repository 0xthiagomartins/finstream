import streamlit as st
from pages.budget_dashboard import render_budget_dashboard
from pages.budget_goals import render_budget_goals_page


def init_session_state():
    """Initialize session state variables."""
    if "current_page" not in st.session_state:
        st.session_state.current_page = "Budget Dashboard"


def main():
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

    # Set custom font
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

            /* Ensure consistent font size */
            .streamlit-expanderHeader, 
            .stMarkdown p, 
            .dataframe td, 
            .dataframe th,
            .stMetric label,
            .stMetric div,
            .stNumberInput label,
            .stTextInput label,
            .stSelectbox label {
                font-size: 14px !important;
            }

            /* Headers */
            h1 { font-size: 28px !important; }
            h2 { font-size: 24px !important; }
            h3 { font-size: 20px !important; }
        </style>
    """,
        unsafe_allow_html=True,
    )

    # Alternative: Create a .streamlit/config.toml file
    # [theme]
    # base="dark"
    # primaryColor="#FF4B4B"
    # backgroundColor="#0E1117"
    # secondaryBackgroundColor="#262730"

    init_session_state()

    # Sidebar
    st.sidebar.title("FinStream")
    st.sidebar.markdown("---")

    # Navigation
    pages = [
        "Budget Dashboard",
        "Budget Goals",
        "Goals & First Million",
        "Assets vs Liabilities",
    ]

    st.session_state.current_page = st.sidebar.radio(
        "Navigate to", pages, index=pages.index(st.session_state.current_page)
    )

    # Main content
    if st.session_state.current_page == "Budget Dashboard":
        render_budget_dashboard()
    elif st.session_state.current_page == "Budget Goals":
        render_budget_goals_page()
    elif st.session_state.current_page == "Goals & First Million":
        st.markdown("Financial goals and projections coming soon...")
    elif st.session_state.current_page == "Assets vs Liabilities":
        st.markdown("Net worth tracking coming soon...")


if __name__ == "__main__":
    main()
