import streamlit as st
from services import CoinGeckoAPI
from datetime import datetime, timedelta
from streamlit_extras.metric_cards import style_metric_cards
from streamlit_extras.switch_page_button import switch_page
from streamlit_extras.add_vertical_space import add_vertical_space
from .marketcapof import create_token_search, display_token_info


def format_roi(value: float, as_percentage: bool = False) -> str:
    """Format ROI value as multiplier or percentage with color indication."""
    is_positive = value >= 1
    if as_percentage:
        percentage = (value - 1) * 100
        formatted = f"{percentage:,.2f}%"
    else:
        formatted = f"{value:,.2f}x"

    color = (
        "#09ab3b" if is_positive else "#ea2829"
    )  # Green for positive, red for negative
    return f'<span style="color: {color}">{formatted}</span>'


def calculate_roi(
    token_data: dict, start_date: datetime, end_date: datetime
) -> tuple[float, float, float]:
    """Calculate ROI between two dates."""
    # Get historical data
    coingecko = CoinGeckoAPI()
    history = coingecko.get_market_chart(
        token_data["id"],
        vs_currency="usd",
        days=(end_date - start_date).days,
    )

    # Find closest prices to our dates
    prices = history["prices"]
    start_price = next(
        price[1]
        for price in prices
        if datetime.fromtimestamp(price[0] / 1000) >= start_date
    )
    end_price = next(
        price[1]
        for price in reversed(prices)
        if datetime.fromtimestamp(price[0] / 1000) <= end_date
    )

    roi = end_price / start_price
    return roi, start_price, end_price


def render_roi_calculator():
    """Render the ROI calculator dashboard."""
    st.title("Compare which coin was most profitable to invest")

    # Initialize session state for display preferences
    if "show_as_percentage" not in st.session_state:
        st.session_state.show_as_percentage = False

    # Token selection columns
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Token A")
        token1, token1_data = create_token_search("first token", "token1")
    with col2:
        st.subheader("Token B")
        token2, token2_data = create_token_search("second token", "token2")

    # Date range selection
    st.markdown("### Select Comparison Period")

    # Calculate date range based on token creation dates
    today = datetime.now().date()
    default_start = today - timedelta(days=365)  # Default to 1 year ago
    min_date = default_start

    if token1_data and token2_data:
        try:
            token1_genesis = datetime.strptime(
                token1_data.get("genesis_date")
                or "2009-01-03",  # Bitcoin genesis date as fallback
                "%Y-%m-%d",
            ).date()
            token2_genesis = datetime.strptime(
                token2_data.get("genesis_date")
                or "2009-01-03",  # Bitcoin genesis date as fallback
                "%Y-%m-%d",
            ).date()
            min_date = max(token1_genesis, token2_genesis)
            default_start = max(min_date, default_start)
        except (ValueError, TypeError):
            st.warning("Could not determine token creation dates. Using default range.")

    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "Start Date",
            value=default_start,
            min_value=min_date,
            max_value=today - timedelta(days=1),
            help="Select the starting date for comparison",
        )
    with col2:
        end_date = st.date_input(
            "End Date",
            value=today,
            min_value=start_date + timedelta(days=1),
            max_value=today,
            help="Select the end date for comparison",
        )

    # Display token info and calculate ROI if both tokens are selected
    if token1 and token2 and token1_data and token2_data:
        st.markdown("---")

        # Display token cards
        col1, col2 = st.columns(2)
        with col1:
            display_token_info(token1, token1_data)
        with col2:
            display_token_info(token2, token2_data)

        # Calculate ROI for both tokens
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())

        try:
            roi1, price1_start, price1_end = calculate_roi(
                token1_data, start_datetime, end_datetime
            )
            roi2, price2_start, price2_end = calculate_roi(
                token2_data, start_datetime, end_datetime
            )

            # Display ROI comparison
            st.markdown("### ROI Comparison")

            # Custom CSS for the comparison cards
            st.markdown(
                """
                <style>
                    .comparison-card {
                        display: flex;
                        align-items: center;
                        padding: 1.5rem;
                        border-radius: 1rem;
                        background: rgba(17, 17, 17, 0.3);
                        margin-bottom: 1rem;
                    }
                    .icon-wrapper {
                        width: 80px;
                        height: 80px;
                        margin-right: 1.5rem;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        background: rgba(255, 255, 255, 0.1);
                        border-radius: 50%;
                    }
                    .details {
                        flex-grow: 1;
                    }
                    .title {
                        font-size: 1.25rem;
                        margin-bottom: 0.5rem;
                    }
                    .percentage {
                        font-size: 1.1rem;
                        margin-bottom: 0.25rem;
                    }
                    .period {
                        font-size: 0.9rem;
                        opacity: 0.8;
                    }
                    .chart-icon {
                        width: 40px;
                        height: 40px;
                        margin-left: 1rem;
                    }
                    .green { color: #09ab3b; }
                    .red { color: #ea2829; }
                    .underlined {
                        border-bottom: 2px dotted rgba(255, 255, 255, 0.2);
                    }
                </style>
                """,
                unsafe_allow_html=True,
            )

            col1, col2 = st.columns(2)

            with col1:
                st.markdown(
                    f"""
                    <div class="comparison-card">
                        <div class="icon-wrapper">
                            <img src="{token1.get('large', '')}" alt="{token1['symbol']}" width="60">
                        </div>
                        <div class="details">
                            <div class="title">
                                {token1['name']} <strong>({token1['symbol'].upper()})</strong>
                            </div>
                            <div class="percentage">
                                had {'an' if roi1 >= 1 else 'a'} 
                                <strong class="underlined">
                                    {'increase' if roi1 >= 1 else 'decrease'}
                                </strong> of 
                                <strong class="{'green' if roi1 >= 1 else 'red'}">
                                    {format_roi(roi1, st.session_state.show_as_percentage)}
                                </strong>
                            </div>
                            <div class="period">
                                from {start_date.strftime('%b. %d, %Y')} - {end_date.strftime('%b. %d, %Y')}
                            </div>
                        </div>
                        <div class="chart-icon">
                            {'📈' if roi1 >= 1 else '📉'}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            with col2:
                st.markdown(
                    f"""
                    <div class="comparison-card">
                        <div class="icon-wrapper">
                            <img src="{token2.get('large', '')}" alt="{token2['symbol']}" width="60">
                        </div>
                        <div class="details">
                            <div class="title">
                                {token2['name']} <strong>({token2['symbol'].upper()})</strong>
                            </div>
                            <div class="percentage">
                                had {'an' if roi2 >= 1 else 'a'} 
                                <strong class="underlined">
                                    {'increase' if roi2 >= 1 else 'decrease'}
                                </strong> of 
                                <strong class="{'green' if roi2 >= 1 else 'red'}">
                                    {format_roi(roi2, st.session_state.show_as_percentage)}
                                </strong>
                            </div>
                            <div class="period">
                                from {start_date.strftime('%b. %d, %Y')} - {end_date.strftime('%b. %d, %Y')}
                            </div>
                        </div>
                        <div class="chart-icon">
                            {'📈' if roi2 >= 1 else '📉'}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            # Toggle button centered
            col1, col2, col3 = st.columns([2, 1, 2])
            with col2:
                if st.button("⇄ Toggle %/×", use_container_width=True):
                    st.session_state.show_as_percentage = (
                        not st.session_state.show_as_percentage
                    )
                    st.rerun()

            # Investment simulation
            st.markdown("### Compare ROI for a specific amount")
            investment_amount = st.number_input(
                "Investment Amount ($)",
                min_value=1.0,
                value=1000.0,
                step=100.0,
                format="%.2f",
            )

            col1, col2 = st.columns(2)
            with col1:
                token1_return = investment_amount * roi1
                profit1 = token1_return - investment_amount
                st.markdown(
                    f"""
                    <div style="padding: 1rem; border-radius: 0.5rem; background: {'rgba(9, 171, 59, 0.1)' if profit1 >= 0 else 'rgba(234, 40, 41, 0.1)'}">
                        <h4 style="margin: 0">{token1['symbol'].upper()} Return</h4>
                        <p style="font-size: 1.5rem; margin: 0.5rem 0">
                            ${token1_return:,.2f}
                        </p>
                        <p style="margin: 0; opacity: 0.8; color: {'#09ab3b' if profit1 >= 0 else '#ea2829'}">
                            {"Profit" if profit1 >= 0 else "Loss"}: ${abs(profit1):,.2f}
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            with col2:
                token2_return = investment_amount * roi2
                profit2 = token2_return - investment_amount
                st.markdown(
                    f"""
                    <div style="padding: 1rem; border-radius: 0.5rem; background: {'rgba(9, 171, 59, 0.1)' if profit2 >= 0 else 'rgba(234, 40, 41, 0.1)'}">
                        <h4 style="margin: 0">{token2['symbol'].upper()} Return</h4>
                        <p style="font-size: 1.5rem; margin: 0.5rem 0">
                            ${token2_return:,.2f}
                        </p>
                        <p style="margin: 0; opacity: 0.8; color: {'#09ab3b' if profit2 >= 0 else '#ea2829'}">
                            {"Profit" if profit2 >= 0 else "Loss"}: ${abs(profit2):,.2f}
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            # Winner announcement
            st.markdown("### Result")
            winner = token1 if roi1 > roi2 else token2
            winner_roi = roi1 if roi1 > roi2 else roi2
            loser = token2 if roi1 > roi2 else token1
            loser_roi = roi2 if roi1 > roi2 else roi1

            st.markdown(
                f"""
                <div style='text-align: center; padding: 2rem; background-color: rgba(206, 126, 0, 0.1); border-radius: 10px;'>
                    <h2 style='margin: 0;'>
                        <span style='color: #ce7e00;'>${winner['symbol'].upper()}</span> 
                        outperformed 
                        <span style='color: #666666;'>${loser['symbol'].upper()}</span>
                        by 
                        <span style='color: #09ab3b;'>{format_roi(winner_roi/loser_roi, st.session_state.show_as_percentage)}</span>
                        <br>between {start_date.strftime('%B %d, %Y')} and {end_date.strftime('%B %d, %Y')}
                    </h2>
                </div>
                """,
                unsafe_allow_html=True,
            )

        except Exception as e:
            st.error(f"Error calculating ROI: {str(e)}")

    # Add explanatory text
    st.markdown("---")
    st.markdown(
        """
        ### What is the ROI Calculator?

        The ROI Calculator is a tool developed by MarketCapOf.com to compare investing in two different cryptocurrencies over a set period. The calculator shows you which cryptocurrency from the two you selected would have brought a better return on investment over a specific period. The initial result is displayed like this: "The Y stock had an increase of 8.57x over a specific period". If you click on "8.57x", you can switch it into a percentage. In the "Compare ROI for a specific amount" field, you can include the amount purchased at the selected starting date. This tool is not meant to be a financial investment tool, as past performance does not guarantee future returns. It's simply a fun tool to check what return you could have gotten by investing in a crypto asset at a time in the past.

        ### How to use the ROI Calculator for Crypto?

        You first need to select the two cryptocurrencies that you want to compare. Then just select the comparison period. The calculator will fetch the data and compare which cryptocurrency would have brought a better return on your investment.

        ### Can I use the calculator for a stock and a cryptocurrency?

        Yes, the calculator can help you compare the growth of a cryptocurrency with that of a stock. You just have to make sure that the cryptocurrency existed at the starting date of the comparison.
        """
    )

    # Add CoinGecko attribution
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
