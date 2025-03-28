import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from services import CoinGeckoAPI
from datetime import datetime, timedelta
from .marketcapof import create_token_search
import time

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

def create_correlation_matrix(price_data: pd.DataFrame) -> pd.DataFrame:
    """Create correlation matrix from price data."""
    return price_data.corr(method='pearson')

def plot_correlation_matrix(corr_matrix: pd.DataFrame, token_images: dict):
    """Create a heatmap visualization of the correlation matrix with token icons."""
    # Create the base heatmap
    heatmap = go.Heatmap(
        z=corr_matrix,
        x=corr_matrix.columns,
        y=corr_matrix.columns,
        zmin=-1,
        zmax=1,
        colorscale=[
            [0.0, '#ea2829'],      # Strong negative correlation (red)
            [0.5, '#ffffff'],      # No correlation (white)
            [1.0, '#09ab3b']       # Strong positive correlation (green)
        ],
        hoverongaps=False,
        hovertemplate=(
            'Correlation between<br>' +
            '%{x} and %{y}<br>' +
            'Value: %{z:.3f}<extra></extra>'
        )
    )

    fig = go.Figure(data=heatmap)

    # Add token icons as images on the diagonal
    for i, symbol in enumerate(corr_matrix.columns):
        if symbol in token_images:
            fig.add_layout_image(
                dict(
                    source=token_images[symbol],
                    x=i,
                    y=i,
                    xref="x",
                    yref="y",
                    sizex=0.8,
                    sizey=0.8,
                    xanchor="center",
                    yanchor="middle"
                )
            )

    fig.update_layout(
        title='Crypto Correlation Matrix',
        height=700,
        width=700,
        xaxis=dict(
            showgrid=False,
            showline=True,
            tickmode='array',
            ticktext=corr_matrix.columns,
            tickvals=list(range(len(corr_matrix.columns)))
        ),
        yaxis=dict(
            showgrid=False,
            showline=True,
            tickmode='array',
            ticktext=corr_matrix.columns,
            tickvals=list(range(len(corr_matrix.columns)))
        )
    )

    return fig

def render_correlation_explanation():
    """Render the explanation of correlation analysis."""
    with st.expander("Understanding Correlation Analysis", expanded=False):
        st.markdown("""
        ### What is Correlation?
        
        Correlation is calculated by using each day as a single data point, and this calculation depends on the selected period. 
        For example, if you select a period of one year, the correlation will be computed from 365 data points.
        
        ### Types of Correlation
        
        - **Positively correlated** variables tend to move together
        - **Negatively correlated** variables move inversely to each other
        - **Uncorrelated** variables move independently of each other
        
        ### Pearson Correlation Coefficient
        
        The Pearson Correlation Coefficient quantifies the estimated strength of the linear association between two variables. 
        It ranges from +1 to -1:
        
        - **+1**: Perfect positive linear correlation
        - **-1**: Perfect negative linear correlation
        - **0**: No linear correlation
        
        ### Interpreting the Values
        
        - **Positive Value** (Green): Indicates a positive correlation between two variables
        - **Negative Value** (Red): Indicates a negative correlation between two variables
        - **Zero** (White): Indicates no correlation between two variables
        
        ### Color Scale
        
        The heatmap uses a color scale to visualize correlations:
        - 🔴 Red: Strong negative correlation
        - ⚪ White: No correlation
        - 🟢 Green: Strong positive correlation
        """)

def get_default_tokens():
    """Get default token data for initial visualization."""
    try:
        coingecko = CoinGeckoAPI()
        default_ids = ['bitcoin', 'ethereum', 'ripple', 'monero', 'taraxa', 'mazze']
        default_tokens = []
        
        for coin_id in default_ids:
            try:
                data = coingecko.get_coin_data(coin_id)
                token = {
                    'id': coin_id,
                    'symbol': data['symbol'],
                    'name': data['name'],
                    'large': data['image']['large']
                }
                default_tokens.append(token)
            except Exception as e:
                st.warning(f"Could not fetch data for {coin_id}: {str(e)}")
                continue
        
        return default_tokens
    except Exception as e:
        st.error(f"⚠️ Error fetching default tokens: {str(e)}")
        return []

def render_correlation_dashboard():
    """Render the crypto correlation dashboard."""
    st.title("Crypto Correlation Analysis")
    
    # Remove API key check since we're using free tier
    
    # Period selection with default to 30 days to avoid rate limits
    period_options = {
        "7 days": 7,
        "30 days": 30,
        "90 days": 90,
        "1 year": 365
    }
    
    selected_period = st.selectbox(
        "Select Analysis Period",
        options=list(period_options.keys()),
        index=1,  # Default to 30 days
        help="Choose the time period for correlation analysis"
    )
    
    # Add quick selection for default view
    use_defaults = st.checkbox(
        "Use Default Tokens (BTC, ETH, XRP, XMR, TARA, MAZZE)",
        help="Quick view with popular cryptocurrencies",
        value=True  # Checked by default
    )
    
    selected_tokens = []
    
    if use_defaults:
        selected_tokens = get_default_tokens()
        
        # Display selected tokens info
        st.markdown("### Selected Default Tokens")
        token_cols = st.columns(len(selected_tokens))
        for idx, token in enumerate(selected_tokens):
            with token_cols[idx]:
                st.image(token['large'], width=64)
                st.markdown(f"**{token['symbol'].upper()}**")
    else:
        # Create container for token selection
        with st.container():
            st.subheader("Select Cryptocurrencies")
            
            # Add token selection fields
            col1, col2 = st.columns(2)
            with col1:
                token1, token1_data = create_token_search("First Token", "token1")
                if token1:
                    selected_tokens.append(token1)
            
            with col2:
                token2, token2_data = create_token_search("Second Token", "token2")
                if token2:
                    selected_tokens.append(token2)
            
            # Optional third token
            col3, col4 = st.columns(2)
            with col3:
                token3, token3_data = create_token_search("Third Token (Optional)", "token3")
                if token3:
                    selected_tokens.append(token3)
            
            with col4:
                token4, token4_data = create_token_search("Fourth Token (Optional)", "token4")
                if token4:
                    selected_tokens.append(token4)
    
    if len(selected_tokens) >= 2:
        with st.spinner("Fetching price data and calculating correlations..."):
            # Fetch price data for all selected tokens
            price_data = {}
            token_images = {}  # Store token images
            
            for token in selected_tokens:
                prices = fetch_price_history(token['id'], period_options[selected_period])
                if prices is not None:
                    symbol = token['symbol'].upper()
                    price_data[symbol] = prices
                    token_images[symbol] = token['large']  # Store token image URL
            
            if len(price_data) >= 2:
                # Create DataFrame with all price data
                df = pd.DataFrame(price_data)
                
                # Calculate correlation matrix
                corr_matrix = create_correlation_matrix(df)
                
                # Plot correlation matrix with token icons
                fig = plot_correlation_matrix(corr_matrix, token_images)
                st.plotly_chart(fig)
                
                # Display correlation table
                st.markdown("### Detailed Correlation Values")
                st.dataframe(
                    corr_matrix.style.format("{:.3f}").background_gradient(
                        cmap='RdYlGn',
                        vmin=-1,
                        vmax=1
                    ),
                    use_container_width=True
                )
            else:
                st.error("Failed to fetch price data for the selected tokens.")
    else:
        st.info("Please select at least 2 cryptocurrencies to analyze correlations.") 
    
    # Render explanation
    render_correlation_explanation()
    
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