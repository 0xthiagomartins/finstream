import streamlit as st


def init_session_state():
    """Initialize session state variables."""
    if "current_page" not in st.session_state:
        st.session_state.current_page = "Budget Dashboard"


def main():
    st.set_page_config(page_title="FinStream", page_icon="💰", layout="wide")

    init_session_state()

    # Sidebar
    st.sidebar.title("FinStream")
    st.sidebar.markdown("---")

    # Navigation
    pages = ["Budget Dashboard", "Goals & First Million", "Assets vs Liabilities"]

    st.session_state.current_page = st.sidebar.radio(
        "Navigate to", pages, index=pages.index(st.session_state.current_page)
    )

    # Main content
    st.title(st.session_state.current_page)

    if st.session_state.current_page == "Budget Dashboard":
        st.markdown("Budget tracking and analysis coming soon...")

    elif st.session_state.current_page == "Goals & First Million":
        st.markdown("Financial goals and projections coming soon...")

    elif st.session_state.current_page == "Assets vs Liabilities":
        st.markdown("Net worth tracking coming soon...")


if __name__ == "__main__":
    main()
