import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from services import CoinGeckoAPI
from .marketcapof import create_token_search
import numpy as np

def fetch_price_history(coin_id: str, days: int) -> pd.Series:
    """Fetch price history for a given coin."""
    try:
        coingecko = CoinGeckoAPI()
        data = coingecko.get_market_chart(coin_id, days=days)
        
        # Convert price data to DataFrame
        prices = pd.DataFrame(data['prices'], columns=['timestamp', 'price'])
        prices['timestamp'] = pd.to_datetime(prices['timestamp'], unit='ms')
        prices.set_index('timestamp', inplace=True)
        
        return prices['price']
    except Exception as e:
        st.error(f"⚠️ Error fetching data for {coin_id}: {str(e)}")
        return None

def calculate_price_ratio(price_a: pd.Series, price_b: pd.Series) -> pd.Series:
    """Calculate the price ratio between two tokens."""
    # Ensure both series have the same index
    common_index = price_a.index.intersection(price_b.index)
    price_a = price_a[common_index]
    price_b = price_b[common_index]
    
    # Calculate ratio
    return price_a / price_b

def calculate_moving_averages(ratio: pd.Series, sma_period: int = 30, ema_period: int = 7) -> tuple:
    """Calculate SMA and EMA for the price ratio."""
    sma = ratio.rolling(window=sma_period).mean()
    ema = ratio.ewm(span=ema_period, adjust=False).mean()
    return sma, ema

def calculate_bollinger_bands(ratio: pd.Series, window: int = 20, num_std: float = 2) -> tuple:
    """Calculate Bollinger Bands for the price ratio."""
    sma = ratio.rolling(window=window).mean()
    std = ratio.rolling(window=window).std()
    upper_band = sma + (std * num_std)
    lower_band = sma - (std * num_std)
    return upper_band, sma, lower_band

def plot_price_ratio(
    ratio: pd.Series,
    token_a: dict,
    token_b: dict,
    show_ma: bool = False,
    show_bollinger: bool = False
) -> go.Figure:
    """Create a line plot of the price ratio with optional indicators."""
    fig = go.Figure()

    # Add main ratio line
    fig.add_trace(
        go.Scatter(
            x=ratio.index,
            y=ratio.values,
            name=f"{token_a['symbol'].upper()}/{token_b['symbol'].upper()}",
            line=dict(color='#ce7e00', width=2),
            hovertemplate=(
                "Date: %{x}<br>" +
                f"{token_a['symbol'].upper()}/{token_b['symbol'].upper()}: %{{y:.4f}}<extra></extra>"
            )
        )
    )

    if show_ma:
        # Calculate and add moving averages
        sma, ema = calculate_moving_averages(ratio)
        fig.add_trace(
            go.Scatter(
                x=sma.index,
                y=sma.values,
                name="SMA 30",
                line=dict(color='#666666', width=1, dash='dash'),
                hovertemplate="SMA 30: %{y:.4f}<extra></extra>"
            )
        )
        fig.add_trace(
            go.Scatter(
                x=ema.index,
                y=ema.values,
                name="EMA 7",
                line=dict(color='#09ab3b', width=1, dash='dash'),
                hovertemplate="EMA 7: %{y:.4f}<extra></extra>"
            )
        )

    if show_bollinger:
        # Calculate and add Bollinger Bands
        upper, middle, lower = calculate_bollinger_bands(ratio)
        fig.add_trace(
            go.Scatter(
                x=upper.index,
                y=upper.values,
                name="Upper Band",
                line=dict(color='#666666', width=1, dash='dot'),
                hovertemplate="Upper Band: %{y:.4f}<extra></extra>"
            )
        )
        fig.add_trace(
            go.Scatter(
                x=middle.index,
                y=middle.values,
                name="Middle Band",
                line=dict(color='#666666', width=1, dash='dash'),
                hovertemplate="Middle Band: %{y:.4f}<extra></extra>"
            )
        )
        fig.add_trace(
            go.Scatter(
                x=lower.index,
                y=lower.values,
                name="Lower Band",
                line=dict(color='#666666', width=1, dash='dot'),
                hovertemplate="Lower Band: %{y:.4f}<extra></extra>",
                fill='tonexty',
                fillcolor='rgba(102, 102, 102, 0.1)'
            )
        )

    fig.update_layout(
        title=f"{token_a['symbol'].upper()}/{token_b['symbol'].upper()} Price Ratio",
        xaxis_title="Date",
        yaxis_title="Ratio",
        height=600,
        template="plotly_dark",
        hovermode="x unified",
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )

    return fig

def render_price_ratio_explanation():
    """Render the explanation of price ratio analysis."""
    with st.expander("Understanding Price Ratio Analysis", expanded=False):
        st.markdown("""
        ### What is Price Ratio?
        
        The price ratio between two tokens shows how many units of Token B are needed to equal the value of one unit of Token A.
        For example, if TARA/ETH = 0.0001, it means you need 0.0001 ETH to buy 1 TARA.
        
        ### How to Interpret the Ratio
        
        - **Ratio > 1**: Token A is more expensive than Token B
        - **Ratio < 1**: Token B is more expensive than Token A
        - **Increasing Ratio**: Token A is gaining value relative to Token B
        - **Decreasing Ratio**: Token B is gaining value relative to Token A
        
        ### Trading Applications
        
        - **Arbitrage**: Identify price discrepancies between different trading pairs
        - **Rotation**: Determine optimal times to switch between tokens
        - **Hedge**: Create balanced portfolios with inversely correlated tokens
        
        ### Technical Indicators
        
        - **SMA (Simple Moving Average)**: Shows the average ratio over a period
        - **EMA (Exponential Moving Average)**: Gives more weight to recent prices
        - **Bollinger Bands**: Indicates volatility and potential reversal points
        """)

def render_price_ratio_dashboard():
    """Render the price ratio dashboard."""
    st.title("Token Price Ratio Analysis")
    
    # Initialize session state for tokens if not exists
    if "token_a" not in st.session_state:
        st.session_state.token_a = None
        st.session_state.token_a_data = None
        st.session_state.token_b = None
        st.session_state.token_b_data = None
    
    # Period selection
    period_options = {
        "24 hours": 1,
        "7 days": 7,
        "30 days": 30,
        "90 days": 90,
        "1 year": 365
    }
    
    selected_period = st.selectbox(
        "Select Analysis Period",
        options=list(period_options.keys()),
        index=1,  # Default to 7 days
        help="Choose the time period for ratio analysis"
    )
    
    # Token selection with swap button
    col1, col2, col3 = st.columns([10, 1, 10])
    
    with col1:
        token_a, token_a_data = create_token_search("First Token (A)", "token_a")
        if token_a:
            st.session_state.token_a = token_a
            st.session_state.token_a_data = token_a_data
    
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
            # Swap tokens in session state
            st.session_state.token_a, st.session_state.token_b = st.session_state.token_b, st.session_state.token_a
            st.session_state.token_a_data, st.session_state.token_b_data = st.session_state.token_b_data, st.session_state.token_a_data
            
            # Swap search fragment states
            st.session_state["token_token_a"], st.session_state["token_token_b"] = st.session_state["token_token_b"], st.session_state["token_token_a"]
            st.session_state["token_data_token_a"], st.session_state["token_data_token_b"] = st.session_state["token_data_token_b"], st.session_state["token_data_token_a"]
            
            # Swap search results
            st.session_state["results_token_a"], st.session_state["results_token_b"] = st.session_state["results_token_b"], st.session_state["results_token_a"]
            
            # Swap search queries
            st.session_state["search_query_token_a"], st.session_state["search_query_token_b"] = st.session_state["search_query_token_b"], st.session_state["search_query_token_a"]
            st.rerun()
    
    with col3:
        token_b, token_b_data = create_token_search("Second Token (B)", "token_b")
        if token_b:
            st.session_state.token_b = token_b
            st.session_state.token_b_data = token_b_data
    
    # Use session state tokens for consistency
    token_a = st.session_state.token_a
    token_b = st.session_state.token_b
    token_a_data = st.session_state.token_a_data
    token_b_data = st.session_state.token_b_data
    
    if token_a and token_b:
        # Display token images and names
        st.markdown("### Selected Tokens")
        col1, col2 = st.columns(2)
        with col1:
            if token_a.get('large'):
                st.image(token_a['large'], width=64)
            st.markdown(f"**{token_a['name']} ({token_a['symbol'].upper()})**")
        with col2:
            if token_b.get('large'):
                st.image(token_b['large'], width=64)
            st.markdown(f"**{token_b['name']} ({token_b['symbol'].upper()})**")
        
        with st.spinner("Fetching price data and calculating ratios..."):
            # Fetch price data for both tokens
            price_a = fetch_price_history(token_a['id'], period_options[selected_period])
            price_b = fetch_price_history(token_b['id'], period_options[selected_period])
            
            if price_a is not None and price_b is not None:
                # Calculate price ratio
                ratio = calculate_price_ratio(price_a, price_b)
                
                # Calculate current ratio and variations
                current_ratio = ratio.iloc[-1]
                ratio_24h = ((ratio.iloc[-1] / ratio.iloc[-2]) - 1) * 100
                ratio_7d = ((ratio.iloc[-1] / ratio.iloc[-8]) - 1) * 100 if len(ratio) > 7 else None
                
                # Display KPI metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric(
                        f"{token_a['symbol'].upper()}/{token_b['symbol'].upper()} Ratio",
                        f"{current_ratio:.4f}",
                        f"{ratio_24h:.2f}% (24h)"
                    )
                with col2:
                    st.metric(
                        f"{token_a['symbol'].upper()} Price",
                        f"${price_a.iloc[-1]:,.8f}",
                        f"{((price_a.iloc[-1] / price_a.iloc[-2]) - 1) * 100:.2f}% (24h)"
                    )
                with col3:
                    st.metric(
                        f"{token_b['symbol'].upper()} Price",
                        f"${price_b.iloc[-1]:,.8f}",
                        f"{((price_b.iloc[-1] / price_b.iloc[-2]) - 1) * 100:.2f}% (24h)"
                    )
                
                # Technical indicators toggle
                col1, col2 = st.columns(2)
                with col1:
                    show_ma = st.checkbox("Show Moving Averages", value=False)
                with col2:
                    show_bollinger = st.checkbox("Show Bollinger Bands", value=False)
                
                # Plot price ratio
                fig = plot_price_ratio(ratio, token_a, token_b, show_ma, show_bollinger)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.error("Failed to fetch price data for the selected tokens.")
    else:
        st.info("Please select two tokens to analyze their price ratio.")
    
    # Render explanation
    render_price_ratio_explanation()
    
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
