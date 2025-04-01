import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from services.fii_comparator_service import FIIComparatorService, RECOMMENDED_GROUPS
import pandas as pd

def render_fii_comparator():
    st.title("FII Comparator")
    
    # Initialize service
    comparator = FIIComparatorService()
    
    # Selection method
    selection_method = st.radio(
        "Select comparison method",
        ["Recommended Groups", "Custom Selection"]
    )
    
    if selection_method == "Recommended Groups":
        selected_group = st.selectbox(
            "Select a group to compare",
            options=list(RECOMMENDED_GROUPS.keys())
        )
        selected_fiis = RECOMMENDED_GROUPS[selected_group]
    else:
        all_fiis = [fii for group in RECOMMENDED_GROUPS.values() for fii in group]
        selected_fiis = st.multiselect(
            "Select FIIs to compare",
            options=sorted(all_fiis),
            default=all_fiis[:5]
        )
    
    if not selected_fiis:
        st.warning("Please select at least one FII to compare")
        return
    
    # Date range selection
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "Start Date",
            value=pd.Timestamp.now() - pd.DateOffset(years=1)
        )
    with col2:
        end_date = st.date_input(
            "End Date",
            value=pd.Timestamp.now()
        )
    
    # Fetch data
    with st.spinner("Fetching data..."):
        prices = comparator.get_historical_prices(
            selected_fiis,
            start_date,
            end_date
        )
        
        if prices.empty:
            st.error("Could not fetch data for the selected FIIs")
            return
        
        # Get fund info
        fund_info = comparator.get_fund_info(selected_fiis)
        
        # Calculate all metrics
        returns = comparator.calculate_returns(prices)
        consistency = comparator.calculate_consistency(prices)
        sharpe = comparator.calculate_sharpe_ratio(prices)
        volatility = comparator.calculate_volatility(prices)
        correlation = comparator.calculate_correlation(prices)
        drawdown = comparator.calculate_drawdown(prices)
        monthly_volatility = comparator.calculate_monthly_volatility(prices)
        accumulated_returns = comparator.calculate_accumulated_returns(prices)
        
        # 1. Performance Chart with accumulated returns
        st.subheader("1. Performance Chart")
        fig_performance = go.Figure()
        
        for col in accumulated_returns.columns:
            fig_performance.add_trace(
                go.Scatter(
                    x=accumulated_returns.index,
                    y=accumulated_returns[col],
                    name=col,
                    mode='lines',
                    hovertemplate="%{y:.2f}%<extra></extra>"
                )
            )
        
        fig_performance.update_layout(
            title="Accumulated Returns (%)",
            yaxis_title="Return (%)",
            hovermode="x unified",
            showlegend=True
        )
        st.plotly_chart(fig_performance, use_container_width=True)
        
        # 2. Historical Returns Table with tooltips
        st.subheader("2. Historical Returns (%)")
        st.dataframe(
            returns.round(2),
            column_config={
                "MONTH": st.column_config.NumberColumn(
                    "MONTH",
                    help="Return over the last month",
                    format="%.2f%%"
                ),
                "YEAR": st.column_config.NumberColumn(
                    "YEAR",
                    help="Return over the last year",
                    format="%.2f%%"
                ),
                "3 MONTHS": st.column_config.NumberColumn(
                    "3 MONTHS",
                    help="Return over the last 3 months",
                    format="%.2f%%"
                ),
                "6 MONTHS": st.column_config.NumberColumn(
                    "6 MONTHS",
                    help="Return over the last 6 months",
                    format="%.2f%%"
                )
            },
            use_container_width=True
        )
        
        # 3. Consistency Table
        st.subheader("3. Consistency Metrics")
        consistency_with_pl = pd.concat([consistency, fund_info], axis=1)
        st.dataframe(
            consistency_with_pl.round(2),
            column_config={
                "POSITIVE MONTHS": st.column_config.NumberColumn(
                    "POSITIVE MONTHS",
                    help="Number of months with positive returns"
                ),
                "NEGATIVE MONTHS": st.column_config.NumberColumn(
                    "NEGATIVE MONTHS",
                    help="Number of months with negative returns"
                ),
                "HIGHEST RETURN": st.column_config.NumberColumn(
                    "HIGHEST RETURN",
                    help="Highest monthly return (%)",
                    format="%.2f%%"
                ),
                "LOWEST RETURN": st.column_config.NumberColumn(
                    "LOWEST RETURN",
                    help="Lowest monthly return (%)",
                    format="%.2f%%"
                ),
                "ABOVE CDI": st.column_config.NumberColumn(
                    "ABOVE CDI",
                    help="Number of months performing above CDI"
                ),
                "BELOW CDI": st.column_config.NumberColumn(
                    "BELOW CDI",
                    help="Number of months performing below CDI"
                ),
                "NET WORTH": st.column_config.NumberColumn(
                    "NET WORTH",
                    help="Current fund net worth",
                    format="$ %.2f"
                ),
                "SHAREHOLDERS": st.column_config.NumberColumn(
                    "SHAREHOLDERS",
                    help="Number of shareholders"
                )
            },
            use_container_width=True
        )
        
        # 4-5. Sharpe Ratio and Volatility side by side
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("4. Sharpe Ratio")
            st.markdown("*Higher values indicate better risk-adjusted returns*")
            st.dataframe(
                sharpe.round(2),
                column_config={
                    "12 MESES": st.column_config.NumberColumn(
                        "12 MESES",
                        help="Sharpe ratio for the last 12 months",
                        format="%.2f"
                    ),
                    "INÍCIO": st.column_config.NumberColumn(
                        "INÍCIO",
                        help="Sharpe ratio since inception",
                        format="%.2f"
                    )
                },
                use_container_width=True
            )
        
        with col2:
            st.subheader("5. Volatility (%)")
            st.markdown("*Lower values indicate lower risk*")
            st.dataframe(
                volatility.round(2),
                column_config={
                    "12 MESES": st.column_config.NumberColumn(
                        "12 MESES",
                        help="Volatility over the last 12 months",
                        format="%.2f%%"
                    ),
                    "INÍCIO": st.column_config.NumberColumn(
                        "INÍCIO",
                        help="Volatility since inception",
                        format="%.2f%%"
                    )
                },
                use_container_width=True
            )
        
        # 7. Risk-Return Chart (melhorado)
        st.subheader("7. Risk vs Return Analysis")
        fig_risk_return = go.Figure()
        
        # Add scatter plot
        fig_risk_return.add_trace(
            go.Scatter(
                x=volatility['12 MESES'],
                y=returns['YEAR'],
                mode='markers+text',
                text=volatility.index,
                textposition='top center',
                marker=dict(
                    size=12,
                    color=returns['YEAR'],
                    colorscale='RdYlGn',
                    showscale=True,
                    colorbar=dict(title="Return (%)")
                ),
                hovertemplate="<b>%{text}</b><br>" +
                            "Risk: %{x:.2f}%<br>" +
                            "Return: %{y:.2f}%<br>" +
                            "<extra></extra>"
            )
        )
        
        # Add quadrant lines
        fig_risk_return.add_hline(y=returns['YEAR'].mean(), line_dash="dash", line_color="gray", opacity=0.5)
        fig_risk_return.add_vline(x=volatility['12 MESES'].mean(), line_dash="dash", line_color="gray", opacity=0.5)
        
        fig_risk_return.update_layout(
            title="Risk vs Return Analysis (Last 12 Months)",
            xaxis_title="Risk (Volatility %)",
            yaxis_title="Return (%)",
            showlegend=False,
            annotations=[
                dict(
                    text="High Return<br>Low Risk",
                    x=volatility['12 MESES'].min(),
                    y=returns['YEAR'].max(),
                    showarrow=False,
                    font=dict(size=10)
                ),
                dict(
                    text="High Return<br>High Risk",
                    x=volatility['12 MESES'].max(),
                    y=returns['YEAR'].max(),
                    showarrow=False,
                    font=dict(size=10)
                ),
                dict(
                    text="Low Return<br>Low Risk",
                    x=volatility['12 MESES'].min(),
                    y=returns['YEAR'].min(),
                    showarrow=False,
                    font=dict(size=10)
                ),
                dict(
                    text="Low Return<br>High Risk",
                    x=volatility['12 MESES'].max(),
                    y=returns['YEAR'].min(),
                    showarrow=False,
                    font=dict(size=10)
                )
            ]
        )
        st.plotly_chart(fig_risk_return, use_container_width=True)
        
        # Create 2x2 layout
        st.subheader("8. Advanced Analysis")
        row1_col1, row1_col2 = st.columns(2)
        row2_col1, row2_col2 = st.columns(2)

        # Row 1, Column 1: Shareholders Distribution
        with row1_col1:
            fig_shareholders = go.Figure()
            
            # Calculate retail holders
            retail_holders = fund_info['SHAREHOLDERS'] - fund_info['INSTITUTIONAL HOLDERS']
            
            # Create stacked bar chart
            fig_shareholders.add_trace(
                go.Bar(
                    name='Retail Holders',
                    x=fund_info.index,
                    y=retail_holders,
                    text=retail_holders.apply(lambda x: f'{x:,.0f}'),
                    textposition='auto',
                    marker_color='lightblue',
                    hovertemplate="<b>%{x}</b><br>" +
                                "Retail Holders: %{y:,.0f}<br>" +
                                "<extra></extra>"
                )
            )
            
            fig_shareholders.add_trace(
                go.Bar(
                    name='Institutional Holders',
                    x=fund_info.index,
                    y=fund_info['INSTITUTIONAL HOLDERS'],
                    text=fund_info['INSTITUTIONAL HOLDERS'].apply(lambda x: f'{x:,.0f}'),
                    textposition='auto',
                    marker_color='darkblue',
                    hovertemplate="<b>%{x}</b><br>" +
                                "Institutional Holders: %{y:,.0f}<br>" +
                                "<extra></extra>"
                )
            )
            
            fig_shareholders.update_layout(
                title="Shareholders Distribution",
                height=400,
                barmode='stack',
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            st.plotly_chart(fig_shareholders, use_container_width=True)

        # Row 1, Column 2: Drawdown Analysis
        with row1_col2:
            fig_drawdown = go.Figure()
            
            for column in drawdown.columns:
                fig_drawdown.add_trace(
                    go.Scatter(
                        x=drawdown.index,
                        y=drawdown[column] * 100,
                        name=column,
                        fill='tonexty',
                        hovertemplate="<b>%{x}</b><br>" +
                                    "Drawdown: %{y:.2f}%<br>" +
                                    "<extra></extra>"
                    )
                )
            
            fig_drawdown.update_layout(
                title="Drawdown Analysis",
                height=400,
                yaxis_title="Drawdown (%)",
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            st.plotly_chart(fig_drawdown, use_container_width=True)

        # Row 2, Column 1: Net Worth Evolution
        with row2_col1:
            fig_net_worth = go.Figure()
            fig_net_worth.add_trace(
                go.Bar(
                    x=fund_info.index,
                    y=fund_info['NET WORTH'],
                    text=fund_info['NET WORTH'].apply(lambda x: f'$ {x:,.0f}'),
                    textposition='auto',
                    marker_color='lightgreen',
                    hovertemplate="<b>%{x}</b><br>" +
                                "Net Worth: $ %{y:,.2f}<br>" +
                                "<extra></extra>"
                )
            )
            fig_net_worth.update_layout(
                title="Net Worth",
                height=400,
                yaxis_title="$",
                showlegend=False
            )
            st.plotly_chart(fig_net_worth, use_container_width=True)

        # Row 2, Column 2: Volatility Evolution
        with row2_col2:
            fig_volatility = go.Figure()
            
            for column in monthly_volatility.columns:
                fig_volatility.add_trace(
                    go.Scatter(
                        x=monthly_volatility.index,
                        y=monthly_volatility[column],
                        name=column,
                        hovertemplate="<b>%{x}</b><br>" +
                                    "Volatility: %{y:.2f}%<br>" +
                                    "<extra></extra>"
                    )
                )
            
            fig_volatility.update_layout(
                title="Volatility Evolution",
                height=400,
                yaxis_title="Volatility (%)",
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            st.plotly_chart(fig_volatility, use_container_width=True)

        # Add correlation matrix with better visualization
        st.subheader("6. Correlation Analysis")
        fig_correlation = go.Figure()
        
        # Create correlation heatmap with new color scheme
        fig_correlation.add_trace(
            go.Heatmap(
                z=correlation,
                x=correlation.columns,
                y=correlation.columns,
                colorscale=[
                    [0.0, 'red'],    # -1 will be red
                    [0.5, 'white'],  # 0 will be white
                    [1.0, 'green']   # 1 will be green
                ],
                zmid=0,
                text=correlation.round(2),
                texttemplate='%{text}',
                textfont={"size": 10},
                hoverongaps=False,
                hovertemplate="<b>%{x}</b> vs <b>%{y}</b><br>" +
                            "Correlation: %{z:.2f}<br>" +
                            "<extra></extra>"
            )
        )
        
        fig_correlation.update_layout(
            title={
                'text': "Correlation Matrix",
                'y':0.95,
                'x':0.5,
                'xanchor': 'center',
                'yanchor': 'top'
            },
            width=800,
            height=800,
            xaxis_showgrid=False,
            yaxis_showgrid=False,
            yaxis_autorange='reversed'
        )
        
        st.plotly_chart(fig_correlation, use_container_width=True) 