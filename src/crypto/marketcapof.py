import streamlit as st
from services import CoinGeckoAPI
import time


def format_large_number(num: float) -> str:
    """Format large numbers in a readable way."""
    if num >= 1_000_000_000_000:  # Trillion
        return f"${num / 1_000_000_000_000:.2f}T"
    elif num >= 1_000_000_000:  # Billion
        return f"${num / 1_000_000_000:.2f}B"
    elif num >= 1_000_000:  # Million
        return f"${num / 1_000_000:.2f}M"
    else:
        return f"${num:,.2f}"


def calculate_theoretical_price(token1_data: dict, token2_data: dict) -> float:
    """Calculate what token1's price would be with token2's market cap."""
    token1_supply = token1_data["market_data"]["circulating_supply"]
    token2_mcap = token2_data["market_data"]["market_cap"]["usd"]

    return token2_mcap / token1_supply


def create_token_search(label: str, key: str) -> tuple:
    """Create a token search interface with results handling."""
    # Add a container with custom styling
    with st.container(border=True):
        st.markdown(
            f"""
            <style>
                [data-testid="stTextInput"] {{
                    background-color: #1E1E1E;
                }}
            </style>
            """,
            unsafe_allow_html=True,
        )

        search_query = st.text_input(
            f"Search {label}",
            key=f"search_{key}",
            placeholder="Enter token name or symbol...",
            help="Type to search for cryptocurrencies",
        )

        selected_token = None
        token_data = None

        if search_query:
            with st.spinner("🔍 Searching..."):
                try:
                    coingecko = CoinGeckoAPI()
                    results = coingecko.search_coins(search_query)

                    if results and results.get("coins"):
                        coins = results["coins"][:5]
                        options = {
                            f"{coin['name']} ({coin['symbol'].upper()})": coin
                            for coin in coins
                        }

                        selected = st.selectbox(
                            "Select token",
                            options.keys(),
                            key=f"select_{key}",
                            help="Choose a token from the search results",
                        )

                        if selected:
                            with st.spinner("📊 Loading token data..."):
                                selected_token = options[selected]
                                token_data = coingecko.get_coin_data(
                                    selected_token["id"]
                                )
                    else:
                        st.warning("⚠️ No results found")
                except Exception as e:
                    st.error(f"🚫 Error: {str(e)}")

        return search_query, selected_token, token_data


def display_token_info(token: dict, token_data: dict = None):
    """Display token information card with enhanced styling."""
    if not token:
        return

    with st.container(border=True):
        # Add custom container styling
        st.markdown(
            """
            <style>
                [data-testid="stContainer"] {
                    background-color: #1E1E1E;
                    border-radius: 10px;
                    padding: 1rem;
                }
            </style>
            """,
            unsafe_allow_html=True,
        )

        col1, col2 = st.columns([1, 3])

        with col1:
            if token.get("large"):
                st.image(token["large"], width=64, use_container_width="never")

        with col2:
            st.markdown(
                f"""
                <h3 style='margin-bottom: 0.5rem;'>
                    {token['name']} 
                    <span style='color: #666;'>({token['symbol'].upper()})</span>
                </h3>
                """,
                unsafe_allow_html=True,
            )

            if token_data:
                price = token_data["market_data"]["current_price"]["usd"]
                mcap = token_data["market_data"]["market_cap"]["usd"]

                # Price metric with custom formatting
                st.metric(
                    label="Price",
                    value=f"${price:,.8f}",
                    help="Current token price in USD",
                )

                # Market cap metric with custom formatting
                st.metric(
                    label="Market Cap",
                    value=format_large_number(mcap),
                    help="Total market capitalization",
                )

                # Add 24h change if available
                if "price_change_percentage_24h" in token_data["market_data"]:
                    change_24h = token_data["market_data"][
                        "price_change_percentage_24h"
                    ]
                    st.metric(
                        label="24h Change",
                        value=f"{change_24h:.2f}%",
                        delta=f"{change_24h:.2f}%",
                        delta_color="normal" if change_24h >= 0 else "inverse",
                    )

            elif token.get("market_cap_rank"):
                st.caption(f"🏆 Rank #{token['market_cap_rank']}")


def display_comparison(
    token1: dict, token1_data: dict, token2: dict, token2_data: dict
):
    """Display enhanced market cap comparison between two tokens."""
    st.markdown(
        """
        <style>
            [data-testid="stMetricValue"] {
                font-size: 1.2rem;
            }
            [data-testid="stMetricDelta"] {
                font-size: 1rem;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Create comparison container
    with st.container(border=True):
        col1, col2, col3 = st.columns([2, 1, 2])

        # Token 1 info
        with col1:
            st.markdown(f"### {token1['symbol'].upper()}")
            st.metric(
                label="Current Price",
                value=f"${token1_data['market_data']['current_price']['usd']:,.8f}",
                help="Current market price",
            )
            st.metric(
                label="Market Cap",
                value=format_large_number(
                    token1_data["market_data"]["market_cap"]["usd"]
                ),
                help="Current market capitalization",
            )

        # Comparison arrow and ratio
        with col2:
            mcap_ratio = (
                token2_data["market_data"]["market_cap"]["usd"]
                / token1_data["market_data"]["market_cap"]["usd"]
            )
            st.markdown(
                f"""
                <div style='text-align: center; font-size: 2rem; margin: 1rem 0;'>
                    ⟶
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.metric(
                label="Market Cap Ratio",
                value=f"{mcap_ratio:.2f}x",
                help=f"How many times larger {token2['symbol'].upper()}'s market cap is",
            )

        # Theoretical price
        with col3:
            theoretical_price = calculate_theoretical_price(token1_data, token2_data)
            current_price = token1_data["market_data"]["current_price"]["usd"]
            price_multiplier = theoretical_price / current_price

            st.markdown(
                f"### If {token1['symbol'].upper()} had {token2['symbol'].upper()}'s market cap"
            )
            st.metric(
                label="Theoretical Price",
                value=f"${theoretical_price:,.8f}",
                delta=f"{price_multiplier:.2f}x from current price",
                delta_color="normal",
                help="Projected price based on market cap comparison",
            )


def render_marketcap_dashboard():
    """Render the enhanced Market Cap Of dashboard."""
    # Header with enhanced styling
    st.title("🔄 Market Cap Of")
    st.markdown(
        """
        <div style='background-color: #1E1E1E; padding: 1rem; border-radius: 5px; margin-bottom: 2rem;'>
            Compare cryptocurrencies by market capitalization and visualize what the price of one token 
            would be if it had the market cap of another. Simply search and select two tokens to compare.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Token selection columns
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📈 Token 1")
        query1, token1, token1_data = create_token_search("first token", "token1")
        if token1:
            display_token_info(token1, token1_data)

    with col2:
        st.subheader("📊 Token 2")
        query2, token2, token2_data = create_token_search("second token", "token2")
        if token2:
            display_token_info(token2, token2_data)

    # Show comparison when both tokens are selected
    if token1 and token2 and token1_data and token2_data:
        st.markdown("---")
        st.subheader("💹 Market Cap Comparison")
        display_comparison(token1, token1_data, token2, token2_data)
