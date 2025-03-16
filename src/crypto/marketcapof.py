import streamlit as st
from services import CoinGeckoAPI


def render_marketcap_dashboard():
    """Render the Market Cap Of dashboard."""
    st.title("Market Cap Of")

    # Initialize CoinGecko API
    coingecko = CoinGeckoAPI()

    # Create two columns for token selection
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Token 1")
        token1_search = st.text_input("Search token", key="token1_search")
        if token1_search:
            results = coingecko.search_coins(token1_search)
            # TODO: Display search results and handle selection

    with col2:
        st.subheader("Token 2")
        token2_search = st.text_input("Search token", key="token2_search")
        if token2_search:
            results = coingecko.search_coins(token2_search)
            # TODO: Display search results and handle selection

    # TODO: Add market cap comparison visualization
    # TODO: Add theoretical price calculation
    # TODO: Add sharing functionality
