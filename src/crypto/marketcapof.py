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


def calculate_theoretical_price(
    token1_data: dict, token2_data: dict, use_ath: bool = False
) -> float:
    """Calculate what token1's price would be with token2's market cap."""
    token1_supply = token1_data["market_data"]["circulating_supply"]

    if use_ath:
        # Use ATH market cap calculation
        ath_price = token2_data["market_data"]["ath"]["usd"]
        current_supply = token2_data["market_data"]["circulating_supply"]
        token2_mcap = ath_price * current_supply
    else:
        # Use current market cap
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
            # Get current and ATH values
            price = token_data["market_data"]["current_price"]["usd"]
            mcap = token_data["market_data"]["market_cap"]["usd"]
            ath_price = token_data["market_data"]["ath"]["usd"]
            ath_date = token_data["market_data"]["ath_date"]["usd"].split("T")[0]
            supply = token_data["market_data"]["circulating_supply"]
            ath_mcap = ath_price * supply
            
            # Main token info row
            col1, col2 = st.columns([1, 4])
            
            with col1:
                if token.get("large"):
                    st.image(token["large"], width=64)
            
            with col2:
                # Token name and symbol with custom styling
                st.markdown(
                    f"""
                    <div style='margin-bottom: 0.5rem;'>
                        <h3 style='margin: 0; color: #FFFFFF;'>
                            {token['name']}
                            <span style='color: #666666; font-size: 0.9em;'>
                                ({token['symbol'].upper()})
                            </span>
                        </h3>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            # Market caps row
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric(
                    label="Current Market Cap",
                    value=format_large_number(mcap),
                    help="Current total market capitalization",
                )

            with col2:
                st.metric(
                    label=f"ATH Market Cap ({ath_date})",
                    value=format_large_number(ath_mcap),
                    help="All-Time High market capitalization",
                )

            # Price row
            price_from_ath = ((price - ath_price) / ath_price) * 100
            col1, col2, col3 = st.columns([1, 4, 1])
            with col2:
                st.metric(
                    label="Current Price",
                    value=f"${price:,.8f}",
                    delta=f"{price_from_ath:.1f}% from ATH",
                    delta_color="normal" if price_from_ath >= 0 else "inverse",
                    help=f"Current price (ATH: ${ath_price:,.8f})",
                )

            # Additional info row
            if token.get("market_cap_rank"):
                st.markdown(
                    f"""
                    <div style='font-size: 0.85em; color: #666666; margin-bottom: 0.5rem;'>
                        🏆 Rank #{token['market_cap_rank']} • 
                        Volume: {format_large_number(token_data['market_data']['total_volume']['usd'])} • 
                        Supply: {format_large_number(supply).replace('$', '')}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        elif token.get("market_cap_rank"):
            # Simplified view when only basic token data is available
            st.markdown(
                f"""
                <div style='display: flex; align-items: center;'>
                    <h3 style='margin: 0;'>{token['name']}</h3>
                    <span style='color: #666666; margin-left: 0.5rem;'>
                        ({token['symbol'].upper()})
                    </span>
                </div>
                <div style='color: #666666; margin-top: 0.25rem;'>
                    🏆 Rank #{token['market_cap_rank']}
                </div>
                """,
                unsafe_allow_html=True,
            )


def display_comparison(
    token1: dict, token1_data: dict, token2: dict, token2_data: dict
):
    """Display enhanced market cap comparison between two tokens."""

    # Add toggle for ATH comparison with better positioning
    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        use_ath = st.toggle(
            f"Compare with {token2['symbol'].upper()} ATH",
            help=(
                f"Toggle between {token2['symbol'].upper()}'s current market cap "
                f"and All-Time High reached on "
                f"{token2_data['market_data']['ath_date']['usd'].split('T')[0]}"
            ),
        )

    # Calculate values for comparison message
    current_mcap = token1_data["market_data"]["market_cap"]["usd"]
    if use_ath:
        target_mcap = (
            token2_data["market_data"]["ath"]["usd"]
            * token2_data["market_data"]["circulating_supply"]
        )
    else:
        target_mcap = token2_data["market_data"]["market_cap"]["usd"]

    # Center title with token names
    title_suffix = "ATH Market Cap of" if use_ath else "Market Cap of"
    st.markdown(
        f"""
        <div style='text-align: center; padding: 1rem;'>
            <h2>
                <b style='color: #ce7e00;'>${token1['symbol'].upper()}</b> 
                With 
                {title_suffix}
                <b style='color: #ce7e00;'>${token2['symbol'].upper()}</b> 
            </h2>
            <p style='color: #666; margin-top: 0.5rem;'>
                {
                    f"ATH Price: ${token2_data['market_data']['ath']['usd']:,.2f} "
                    f"({token2_data['market_data']['ath_date']['usd'].split('T')[0]})"
                    if use_ath else
                    f"Current Price: ${token2_data['market_data']['current_price']['usd']:,.2f}"
                }
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Calculate values
    theoretical_price = calculate_theoretical_price(token1_data, token2_data, use_ath)
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
            mcap_difference = abs(target_mcap - current_mcap)
            is_under = current_mcap < target_mcap

            # Add comparative message
            st.markdown(
                f"""
                <div style='text-align: center; padding: 0.5rem; margin-bottom: 1rem;'>
                    <p style='font-size: 1.8rem; margin: 0;'>
                        <b style='color: #ce7e00;'>{token1['symbol'].upper()}</b> is 
                        <span style='color: {"#ea2829" if not is_under else "#09ab3b"};'>
                            {format_large_number(mcap_difference)} 
                            {"under" if is_under else "above"}
                        </span> 
                        <b style='color: #ce7e00;'>{token2['symbol'].upper()}</b>
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
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
    with col2:
        st.subheader("Token 2")
        token2, token2_data = create_token_search("second token", "token2")

    if (token1 and isinstance(token1, dict)) and (token2 and isinstance(token2, dict)):
        col1, col2, col3 = st.columns([10, 1, 10])

        with col1:
            display_token_info(token1, token1_data)
            st.session_state.token1 = token1
            st.session_state.token1_data = token1_data

        with col2:
            # Center the swap button vertically with custom styling
            st.markdown(
                """
                <style>
                    div[data-testid="column"]:nth-of-type(2) {
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        min-height: 200px;
                    }
                    
                    div[data-testid="column"]:nth-of-type(2) button {
                        background: none;
                        border: none;
                        border-radius: 50%;
                        width: 48px !important;
                        height: 48px;
                        padding: 12px;
                        transition: all 0.2s ease;
                    }
                    
                    div[data-testid="column"]:nth-of-type(2) button:hover {
                        background: rgba(206, 126, 0, 0.1);
                    }
                </style>
                """,
                unsafe_allow_html=True,
            )
            st.markdown(
                "<div style='text-align: center; padding-bottom: 10rem;'></div>",
                unsafe_allow_html=True,
            )
            if st.button(
                "⇄",  # Unicode swap arrow
                help="Swap tokens",
                use_container_width=True,
            ):
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

        with col3:
            display_token_info(token2, token2_data)
            st.session_state.token2 = token2
            st.session_state.token2_data = token2_data

    # Show comparison when both tokens are selected
    if (
        st.session_state.token1
        and st.session_state.token2
        and st.session_state.token1_data
        and st.session_state.token2_data
    ):
        display_comparison(
            st.session_state.token1,
            st.session_state.token1_data,
            st.session_state.token2,
            st.session_state.token2_data,
        )

    # Add CoinGecko attribution at the bottom
    st.markdown(
        """
        <div style='position: fixed; bottom: 0; right: 0; padding: 1rem; 
             background-color: #1E1E1E; border-top-left-radius: 5px;'>
            <a href='https://www.coingecko.com/' target='_blank' 
               style='color: #666; text-decoration: none; font-size: 0.8rem;'>
                Data powered by CoinGecko
            </a>
        </div>
        """,
        unsafe_allow_html=True,
    )
