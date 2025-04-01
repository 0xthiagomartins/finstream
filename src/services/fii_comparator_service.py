from datetime import datetime, timedelta
from functools import lru_cache
import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict, List, Optional

# Recommended FII groups
RECOMMENDED_GROUPS = {
    'Multimercado': [
        'HGFF11', 'RBRF11', 'KFOF11', 'XPFI11', 'URFP11'
    ],
    'Renda Fixa': [
        'KNIP11', 'KNCR11', 'VGIR11', 'RCRB11', 'BTCR11'
    ],
    'Ações': [
        'HGLG11', 'XPLG11', 'VILG11', 'BRCO11', 'LVBI11'
    ],
    'Previdência': [
        'HGPO11', 'VGHF11', 'HGRU11', 'VCJR11', 'VGIP11'
    ],
    'Cambial': [
        'EURO11', 'USHY11', 'JPUS11', 'EUSD11', 'GSFI11'
    ]
}

class FIIComparatorService:
    def __init__(self):
        self.cdi_rate = 0.1365  # Current CDI rate (13.65%)
        self.cdi_daily = (1 + self.cdi_rate) ** (1/252) - 1

    def get_historical_prices(self, tickers: List[str], start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Get historical prices for multiple FIIs"""
        all_prices = {}
        for ticker in tickers:
            try:
                fii = yf.Ticker(f"{ticker}.SA")
                hist = fii.history(start=start_date, end=end_date)
                all_prices[ticker] = hist['Close']
            except Exception as e:
                print(f"Error fetching data for {ticker}: {str(e)}")
        
        return pd.DataFrame(all_prices)

    def calculate_returns(self, prices: pd.DataFrame) -> pd.DataFrame:
        """Calculate returns for different periods"""
        returns = pd.DataFrame()
        
        # Calculate different period returns
        returns['MONTH'] = prices.pct_change(periods=21).iloc[-1]  # ~1 month of trading days
        returns['YEAR'] = prices.pct_change(periods=252).iloc[-1]  # ~1 year of trading days
        returns['3 MONTHS'] = prices.pct_change(periods=63).iloc[-1]  # ~3 months
        returns['6 MONTHS'] = prices.pct_change(periods=126).iloc[-1]  # ~6 months
        
        return returns * 100  # Convert to percentage

    def calculate_consistency(self, prices: pd.DataFrame) -> pd.DataFrame:
        """Calculate consistency metrics"""
        monthly_returns = prices.pct_change()
        
        consistency = pd.DataFrame(index=prices.columns)
        consistency['POSITIVE MONTHS'] = (monthly_returns > 0).sum()
        consistency['NEGATIVE MONTHS'] = (monthly_returns < 0).sum()
        consistency['HIGHEST RETURN'] = monthly_returns.max() * 100
        consistency['LOWEST RETURN'] = monthly_returns.min() * 100
        consistency['ABOVE CDI'] = (monthly_returns > self.cdi_daily).sum()
        consistency['BELOW CDI'] = (monthly_returns < self.cdi_daily).sum()
        
        return consistency

    def calculate_sharpe_ratio(self, prices: pd.DataFrame) -> pd.DataFrame:
        """Calculate Sharpe ratio"""
        returns = prices.pct_change().dropna()
        
        # Calculate excess returns over risk-free rate
        rf_daily = (1 + self.cdi_rate) ** (1/252) - 1
        excess_returns = returns - rf_daily
        
        # Calculate Sharpe ratio
        sharpe = pd.DataFrame(index=prices.columns)
        sharpe['12 MESES'] = (
            np.sqrt(252) * excess_returns.tail(252).mean() / 
            excess_returns.tail(252).std()
        )
        sharpe['INÍCIO'] = (
            np.sqrt(252) * excess_returns.mean() / 
            excess_returns.std()
        )
        
        return sharpe

    def calculate_volatility(self, prices: pd.DataFrame) -> pd.DataFrame:
        """Calculate volatility"""
        returns = prices.pct_change().dropna()
        
        volatility = pd.DataFrame(index=prices.columns)
        volatility['12 MESES'] = returns.tail(252).std() * np.sqrt(252) * 100
        volatility['INÍCIO'] = returns.std() * np.sqrt(252) * 100
        
        return volatility

    def calculate_correlation(self, prices: pd.DataFrame) -> pd.DataFrame:
        """Calculate correlation matrix"""
        returns = prices.pct_change().dropna()
        return returns.corr()

    def calculate_drawdown(self, prices: pd.DataFrame) -> pd.DataFrame:
        """Calculate drawdown series"""
        return prices / prices.expanding().max() - 1

    def get_fund_info(self, tickers: List[str]) -> pd.DataFrame:
        """Get detailed fund information"""
        fund_info = {}
        for ticker in tickers:
            try:
                fii = yf.Ticker(f"{ticker}.SA")
                info = fii.info
                
                # Get holders information
                major_holders = fii.major_holders
                institutional_holders = fii.institutional_holders
                
                # Calculate total holders from major holders if available
                total_holders = 0
                if isinstance(major_holders, pd.DataFrame) and not major_holders.empty:
                    try:
                        # Handle both string and float percentage values
                        pct_value = major_holders.iloc[0, 0]
                        if isinstance(pct_value, str):
                            institutional_pct = float(pct_value.strip('%')) / 100
                        else:
                            institutional_pct = float(pct_value) / 100
                        
                        total_holders = int(info.get('floatShares', 0) * institutional_pct)
                    except (ValueError, TypeError, IndexError) as e:
                        print(f"Error processing major holders for {ticker}: {str(e)}")
                        total_holders = info.get('floatShares', 0)
                
                # Add institutional holders count if available
                inst_holders_count = (
                    len(institutional_holders) if isinstance(institutional_holders, pd.DataFrame) 
                    else 0
                )
                
                # Fallback to floatShares if no holder information is available
                if total_holders == 0:
                    total_holders = info.get('floatShares', 0)
                
                fund_info[ticker] = {
                    'NET WORTH': info.get('totalAssets', 0),
                    'SHAREHOLDERS': total_holders,
                    'CURRENT PRICE': info.get('regularMarketPrice', 0),
                    'MARKET CAP': info.get('marketCap', 0),
                    'TRADING VOLUME': info.get('averageVolume', 0),
                    'INSTITUTIONAL HOLDERS': inst_holders_count,
                }
                
            except Exception as e:
                print(f"Error fetching info for {ticker}: {str(e)}")
                fund_info[ticker] = {
                    'NET WORTH': 0,
                    'SHAREHOLDERS': 0,
                    'CURRENT PRICE': 0,
                    'MARKET CAP': 0,
                    'TRADING VOLUME': 0,
                    'INSTITUTIONAL HOLDERS': 0,
                }
        
        return pd.DataFrame.from_dict(fund_info, orient='index')

    def calculate_pl_per_shareholder(self, fund_info: pd.DataFrame) -> pd.Series:
        """Calculate average equity per shareholder"""
        return fund_info['NET WORTH'] / fund_info['SHAREHOLDERS']

    def calculate_monthly_volatility(self, prices: pd.DataFrame) -> pd.DataFrame:
        """Calculate monthly volatility series"""
        returns = prices.pct_change().dropna()
        volatility = returns.rolling(21).std() * np.sqrt(252) * 100
        return volatility

    def calculate_accumulated_returns(self, prices: pd.DataFrame) -> pd.DataFrame:
        """Calculate accumulated returns series"""
        return (prices / prices.iloc[0] - 1) * 100 