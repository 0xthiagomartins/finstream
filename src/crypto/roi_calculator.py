import streamlit as st
from services import CoinGeckoAPI
from datetime import datetime, timedelta
from streamlit_extras.metric_cards import style_metric_cards
from streamlit_extras.switch_page_button import switch_page
from streamlit_extras.add_vertical_space import add_vertical_space
from .marketcapof import create_token_search, display_token_info
import plotly.graph_objects as go
from components.icons import Icons


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
) -> tuple[float, float, float, list, list]:
    """Calculate ROI between two dates and return price history."""
    # Get historical data
    coingecko = CoinGeckoAPI()
    history = coingecko.get_market_chart(
        token_data["id"],
        vs_currency="usd",
        days=(end_date - start_date).days,
    )

    # Process all prices for the chart
    prices = history["prices"]
    dates = [datetime.fromtimestamp(price[0] / 1000) for price in prices]
    values = [price[1] for price in prices]

    # Find closest prices to our dates for ROI calculation
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
    return roi, start_price, end_price, dates, values


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

        # Calculate ROI for both tokens
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())

        try:
            # Get ROI and price history for both tokens
            roi1, price1_start, price1_end, dates1, values1 = calculate_roi(
                token1_data, start_datetime, end_datetime
            )
            roi2, price2_start, price2_end, dates2, values2 = calculate_roi(
                token2_data, start_datetime, end_datetime
            )

            token1_color = "#ce7e00"  # Orange for token1
            token2_color = "#1f77b4"  # Blue for token2

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
                        width: 100px;
                        height: 100px;
                        margin-left: 1rem;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                    }
                    .icon-grow {
                        fill: #09ab3b;
                    }
                    .icon-decline {
                        fill: #ea2829;
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

            # Display ROI comparison cards
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
                            {Icons.TREND_UP if roi1 >= 1 else Icons.TREND_DOWN}
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
                            {Icons.TREND_UP if roi2 >= 1 else Icons.TREND_DOWN}
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

            # Create two columns for layout
            left_col, right_col = st.columns([3, 5])

            with left_col:
                st.markdown(
                    '<div style="padding-bottom: 2rem;"></div>', unsafe_allow_html=True
                )
                investment_amount = st.number_input(
                    "Investment Amount ($)",
                    min_value=1.0,
                    value=1000.0,
                    step=100.0,
                    format="%.2f",
                )
                st.markdown(
                    '<div style="padding-bottom: 4rem;"></div>', unsafe_allow_html=True
                )

                col1, col2 = st.columns(2)
                with col1:
                    token1_return = investment_amount * roi1
                    profit1 = token1_return - investment_amount
                    st.metric(
                        f'{token1["symbol"].upper()} Return',
                        f"${token1_return:,.2f}",
                        delta=f"{profit1:,.2f}",
                        delta_color=f"normal",
                    )

                with col2:
                    token2_return = investment_amount * roi2
                    profit2 = token2_return - investment_amount
                    st.metric(
                        f'{token2["symbol"].upper()} Return',
                        f"${token2_return:,.2f}",
                        delta=f"{profit2:,.2f}",
                        delta_color=f"normal",
                    )

            with right_col:
                # Create comparison plot
                fig = go.Figure()

                # Add lines for both tokens with actual amounts
                fig.add_trace(
                    go.Scatter(
                        x=dates1,
                        y=[v * (investment_amount / price1_start) for v in values1],
                        name=f"{token1['symbol'].upper()}",
                        line=dict(
                            color=token1_color,
                            width=2,
                        ),
                        hovertemplate=(
                            f"{token1['symbol'].upper()}<br>"
                            "Date: %{x|%Y-%m-%d}<br>"
                            "Value: $%{y:,.2f}<br>"
                            "<extra></extra>"
                        ),
                    )
                )

                fig.add_trace(
                    go.Scatter(
                        x=dates2,
                        y=[v * (investment_amount / price2_start) for v in values2],
                        name=f"{token2['symbol'].upper()}",
                        line=dict(
                            color=token2_color,
                            width=2,
                        ),
                        hovertemplate=(
                            f"{token2['symbol'].upper()}<br>"
                            "Date: %{x|%Y-%m-%d}<br>"
                            "Value: $%{y:,.2f}<br>"
                            "<extra></extra>"
                        ),
                    )
                )

                # Add reference line at initial investment
                fig.add_hline(
                    y=investment_amount,
                    line_dash="dash",
                    line_color="#666666",
                    annotation_text="Initial Investment",
                    annotation_position="right",
                )

                # Update layout
                fig.update_layout(
                    title="Investment Value Over Time",
                    yaxis_title="Value ($)",
                    plot_bgcolor="#0E1117",
                    paper_bgcolor="#0E1117",
                    font=dict(color="#FFFFFF"),
                    showlegend=True,
                    legend=dict(
                        yanchor="top",
                        y=0.99,
                        xanchor="left",
                        x=0.01,
                        bgcolor="rgba(0,0,0,0)",
                    ),
                    hovermode="x unified",
                    yaxis=dict(
                        gridcolor="#2e3026",
                        tickformat="$,.0f",
                        zeroline=False,
                    ),
                    xaxis=dict(
                        gridcolor="#2e3026",
                        type="date",
                    ),
                    margin=dict(t=30, r=10, b=10, l=10),
                )

                st.plotly_chart(fig, use_container_width=True)

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
