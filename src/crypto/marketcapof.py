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

    @st.cache_data(ttl=300)  # Increased cache time to 5 minutes
    def search_tokens(query: str):
        if not query or len(query) < 2:
            return []
        try:
            coingecko = CoinGeckoAPI()
            results = coingecko.search_coins(query)
            if results and results.get("coins"):
                return results["coins"][:5]
            return []
        except Exception:
            return []

    # Initialize session state
    if f"search_{key}" not in st.session_state:
        st.session_state[f"search_{key}"] = ""
        st.session_state[f"token_{key}"] = None
        st.session_state[f"token_data_{key}"] = None
        st.session_state[f"results_{key}"] = None
        st.session_state[f"last_search_{key}"] = time.time()
        st.session_state[f"search_query_{key}"] = ""

    @st.fragment
    def token_search_fragment():
        with st.container(border=True):
            # Search form with submit button
            with st.form(key=f"search_form_{key}", clear_on_submit=False):
                search_query = st.text_input(
                    f"Search {label}",
                    key=f"search_input_{key}",
                    placeholder="Enter token name or symbol (min. 2 chars)",
                    help="Type to search for cryptocurrencies",
                )

                search_submitted = st.form_submit_button(
                    "🔍 Search",
                    use_container_width=True,
                )

            # Only search if form was submitted and query is valid
            if search_submitted and search_query and len(search_query.strip()) >= 2:
                st.session_state[f"search_query_{key}"] = search_query
                with st.spinner("🔍"):
                    results = search_tokens(search_query.lower().strip())
                    if results:
                        st.session_state[f"results_{key}"] = results
                    else:
                        st.warning("⚠️ No results found")
                        st.session_state[f"results_{key}"] = None

            # Show selectbox if we have results
            if st.session_state[f"results_{key}"]:
                options = {
                    f"{coin['name']} ({coin['symbol'].upper()})": coin
                    for coin in st.session_state[f"results_{key}"]
                }

                selected = st.selectbox(
                    "Select token",
                    options=[""] + list(options.keys()),
                    key=f"select_{key}",
                    help="Choose a token from the search results",
                )

                if selected and selected in options:
                    token = options[selected]

                    # Only fetch token data if it's a new selection
                    if (
                        not st.session_state[f"token_{key}"]
                        or st.session_state[f"token_{key}"]["id"] != token["id"]
                    ):
                        with st.spinner("📊 Loading token data..."):
                            try:
                                coingecko = CoinGeckoAPI()
                                token_data = coingecko.get_coin_data(token["id"])
                                st.session_state[f"token_{key}"] = token
                                st.session_state[f"token_data_{key}"] = token_data
                                st.rerun()
                            except Exception as e:
                                st.error(f"🚫 Error: {str(e)}")

    # Call the fragment
    token_search_fragment()

    return (
        st.session_state.get(f"token_{key}"),
        st.session_state.get(f"token_data_{key}"),
    )


def display_token_info(token: dict, token_data: dict = None):
    """Display token information card with enhanced styling."""
    if not token:
        return

    with st.container(border=True):

        if token_data:
            price = token_data["market_data"]["current_price"]["usd"]
            mcap = token_data["market_data"]["market_cap"]["usd"]
            col1, col2 = st.columns([1, 1])

            with col1:
                if token.get("large"):
                    st.image(token["large"], width=64, use_container_width="never")
                # Price metric with custom formatting
                st.metric(
                    label="Price",
                    value=f"${price:,.8f}",
                    help="Current token price in USD",
                )

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
                # Market cap metric with custom formatting
                st.metric(
                    label="Market Cap",
                    value=format_large_number(mcap),
                    help="Total market capitalization",
                )

        elif token.get("market_cap_rank"):
            st.caption(f"🏆 Rank #{token['market_cap_rank']}")


def display_comparison(
    token1: dict, token1_data: dict, token2: dict, token2_data: dict
):
    """Display enhanced market cap comparison between two tokens."""

    # Center title with token names
    st.markdown(
        f"""
        <div style='text-align: center; padding: 2rem;'>
            <h2>
                <b style='color: #ce7e00;'>${token1['symbol']}</b> With The Market Cap of <b style='color: #ce7e00;'>${token2['symbol']}</b>
            </h2>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Calculate values
    theoretical_price = calculate_theoretical_price(token1_data, token2_data)
    current_price = token1_data["market_data"]["current_price"]["usd"]
    price_multiplier = theoretical_price / current_price

    # Create centered container for comparison
    with st.container():
        # Center the content
        col1, col2, col3 = st.columns([2, 3, 2])

        with col2:
            # Token image and price comparison
            subcol1, subcol2 = st.columns([1, 4])
            with subcol1:
                if token1.get("large"):
                    st.image(token1["large"])

            with subcol2:
                # Invert the delta color logic: green if > 1, red if < 1
                st.metric(
                    label=token1["symbol"].upper(),
                    value=f"${theoretical_price:,.8f}",
                    delta=f"{price_multiplier:.2f}x",
                    delta_color="normal" if price_multiplier > 1 else "inverse",
                )

    # Additional market cap details in a container below
    with st.container(border=True):
        col1, col2, col3 = st.columns(3)

        # Current market cap
        with col1:
            st.metric(
                label=f"{token1['symbol'].upper()} Market Cap",
                value=format_large_number(
                    token1_data["market_data"]["market_cap"]["usd"]
                ),
                help="Current market capitalization",
            )

        # Arrow and multiplier
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
                label="Market Cap Difference",
                value=f"{mcap_ratio:.2f}x",
                help=f"How many times larger {token2['symbol'].upper()}'s market cap is",
            )

        # Target market cap
        with col3:
            st.metric(
                label=f"{token2['symbol'].upper()} Market Cap",
                value=format_large_number(
                    token2_data["market_data"]["market_cap"]["usd"]
                ),
                help="Target market capitalization",
            )


def render_marketcap_dashboard():
    """Render the enhanced Market Cap Of dashboard."""
    # Initialize session state for token data if not exists
    if "token1" not in st.session_state:
        st.session_state.token1 = None
        st.session_state.token1_data = None
        st.session_state.token2 = None
        st.session_state.token2_data = None

    # Header with enhanced styling
    st.title("Market Cap Of")
    st.markdown(
        """
        <div style='background-color: #1E1E1E; padding: 1rem; border-radius: 5px; margin-bottom: 2rem;'>
            Compare cryptocurrencies by market capitalization. Type to search and select tokens to compare.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Token selection columns
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Token 1")
        token1, token1_data = create_token_search("first token", "token1")
        if token1 and isinstance(token1, dict):
            display_token_info(token1, token1_data)
            # Update main session state
            st.session_state.token1 = token1
            st.session_state.token1_data = token1_data

    with col2:
        st.subheader("Token 2")
        token2, token2_data = create_token_search("second token", "token2")
        if token2 and isinstance(token2, dict):
            display_token_info(token2, token2_data)
            # Update main session state
            st.session_state.token2 = token2
            st.session_state.token2_data = token2_data

    # Show comparison when both tokens are selected
    if (
        st.session_state.token1
        and st.session_state.token2
        and st.session_state.token1_data
        and st.session_state.token2_data
    ):

        # Add invert comparison button
        col1, col2, col3 = st.columns([2, 1, 2])
        with col2:
            if st.button("🔄 Invert Comparison", use_container_width=True):
                # Swap main tokens
                (
                    st.session_state.token1,
                    st.session_state.token2,
                ) = (
                    st.session_state.token2,
                    st.session_state.token1,
                )

                # Swap token data
                (
                    st.session_state.token1_data,
                    st.session_state.token2_data,
                ) = (
                    st.session_state.token2_data,
                    st.session_state.token1_data,
                )

                # Swap search fragment states
                (
                    st.session_state["token_token1"],
                    st.session_state["token_token2"],
                ) = (
                    st.session_state["token_token2"],
                    st.session_state["token_token1"],
                )

                (
                    st.session_state["token_data_token1"],
                    st.session_state["token_data_token2"],
                ) = (
                    st.session_state["token_data_token2"],
                    st.session_state["token_data_token1"],
                )

                # Swap search results
                (
                    st.session_state["results_token1"],
                    st.session_state["results_token2"],
                ) = (
                    st.session_state["results_token2"],
                    st.session_state["results_token1"],
                )

                # Swap search queries
                (
                    st.session_state["search_query_token1"],
                    st.session_state["search_query_token2"],
                ) = (
                    st.session_state["search_query_token2"],
                    st.session_state["search_query_token1"],
                )

                st.rerun()

        display_comparison(
            st.session_state.token1,
            st.session_state.token1_data,
            st.session_state.token2,
            st.session_state.token2_data,
        )
