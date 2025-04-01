from datetime import datetime, timedelta
from functools import lru_cache
import yfinance as yf
import pandas as pd
from typing import Dict, List, Optional
import numpy as np

# Lista de FIIs por setor
FIIS_POR_SETOR = {
    'Logistics': [
        'HGLG11', 'XPLG11', 'VILG11', 'BRCO11', 'LVBI11'
    ],
    'Shopping Malls': [
        'XPML11', 'VISC11', 'HSML11', 'MALL11', 'VRTA11'
    ],
    'Offices': [
        'KNRI11', 'PVBI11', 'RCRB11', 'BRCR11', 'HGRE11'
    ],
    'Receivables': [
        'KNIP11', 'KNCR11', 'MXRF11', 'RECT11', 'VCJR11'
    ],
    'Hybrid': [
        'GGRC11', 'RBRR11', 'RBRF11', 'VGIR11', 'VGHF11'
    ],
    'Others': [
        'BTLG11', 'HCTR11', 'VINO11', 'TRXF11', 'SDIL11'
    ]
}

class FIIService:
    def __init__(self):
        self.last_update = None
        self.update_interval = timedelta(hours=12)  # 12 horas entre atualizações

    @staticmethod
    def _get_current_cache_key() -> str:
        """Gera uma chave de cache baseada no período do dia (manhã/tarde)"""
        now = datetime.now()
        # Chave única para cada período de 12 horas
        period = "AM" if now.hour < 12 else "PM"
        return f"{now.date()}_{period}"

    @lru_cache(maxsize=2)  # Mantém cache para dois períodos
    def _fetch_fii_data_cached(self, cache_key: str) -> Dict:
        """Fetch FII data with cache"""
        all_fiis_data = {}
        
        for setor, fiis in FIIS_POR_SETOR.items():
            for fii in fiis:
                try:
                    ticker = yf.Ticker(f"{fii}.SA")
                    info = ticker.info
                    
                    # Get historical dividends
                    end_date = pd.Timestamp.now(tz='America/Sao_Paulo')
                    start_date = end_date - pd.DateOffset(years=1)
                    dividends = ticker.dividends
                    
                    if len(dividends) > 0:
                        dividends = dividends.tz_localize(None)
                        recent_dividends = dividends[
                            (dividends.index >= start_date.tz_localize(None)) & 
                            (dividends.index <= end_date.tz_localize(None))
                        ]
                        dy_12m = (recent_dividends.sum() / info.get('regularMarketPrice', 0)) * 100
                    else:
                        dy_12m = 0
                    
                    # Get financial metrics
                    all_fiis_data[fii] = {
                        'setor': setor,
                        'preco_atual': info.get('regularMarketPrice', 0),
                        'p_vp': info.get('priceToBook', 0),
                        'dy_12m': dy_12m,
                        'patrimonio_liquido': info.get('totalAssets', 0),
                    }
                except Exception as e:
                    print(f"Error fetching data for {fii}: {str(e)}")
                    continue
        
        return all_fiis_data

    def get_fii_data(self, renda_desejada: float) -> pd.DataFrame:
        """
        Returns DataFrame with FIIs data and calculations to achieve desired income
        """
        cache_key = self._get_current_cache_key()
        fii_data = self._fetch_fii_data_cached(cache_key)
        
        # Convert to DataFrame
        df = pd.DataFrame.from_dict(fii_data, orient='index')
        
        # Check if we have valid data
        if df.empty:
            return pd.DataFrame(columns=[
                'SECTOR', 'CURRENT PRICE ($)', 'P/BV', 'DY (12M) %',
                'NET WORTH', 'REQUIRED SHARES', 'REQUIRED INVESTMENT ($)'
            ])
        
        # Calculate required shares and investment with zero division handling
        df['qtd_necessaria'] = df.apply(
            lambda row: np.ceil(
                (renda_desejada / len(df)) / (row['preco_atual'] * (row['dy_12m'] / 100 / 12))
            ) if row['preco_atual'] > 0 and row['dy_12m'] > 0 else 0,
            axis=1
        )
        
        df['valor_necessario'] = df.apply(
            lambda row: row['qtd_necessaria'] * row['preco_atual'] 
            if row['preco_atual'] > 0 else 0,
            axis=1
        )
        
        # Replace infinity and NaN with 0
        df = df.replace([np.inf, -np.inf], 0)
        df = df.fillna(0)
        
        # Rename columns to English
        df = df.rename(columns={
            'setor': 'SECTOR',
            'preco_atual': 'CURRENT PRICE ($)',
            'p_vp': 'P/BV',
            'dy_12m': 'DY (12M) %',
            'patrimonio_liquido': 'NET WORTH',
            'qtd_necessaria': 'REQUIRED SHARES',
            'valor_necessario': 'REQUIRED INVESTMENT ($)'
        })
        
        # Sort by sector and DY
        df = df.sort_values(['SECTOR', 'DY (12M) %'], ascending=[True, False])
        
        return df 

    def get_detailed_fii_info(self, ticker_code: str) -> Optional[Dict]:
        """Get detailed financial information for a FII"""
        try:
            ticker = yf.Ticker(f"{ticker_code}.SA")
            info = ticker.info
            
            # Get financial statements
            financials = ticker.financials
            balance_sheet = ticker.balance_sheet
            cashflow = ticker.cashflow
            
            # Prepare valuation measures
            valuation_measures = {
                "Market Cap": info.get('marketCap'),
                "Enterprise Value": info.get('enterpriseValue'),
                "Trailing P/E": info.get('trailingPE'),
                "Forward P/E": info.get('forwardPE'),
                "PEG Ratio": info.get('pegRatio'),
                "Price/Sales": info.get('priceToSalesTrailing12Months'),
                "Price/Book": info.get('priceToBook'),
                "Enterprise Value/Revenue": info.get('enterpriseToRevenue'),
                "Enterprise Value/EBITDA": info.get('enterpriseToEbitda')
            }
            
            # Prepare financial highlights
            financial_highlights = {
                "Profit Margin": info.get('profitMargins'),
                "Return on Assets": info.get('returnOnAssets'),
                "Return on Equity": info.get('returnOnEquity'),
                "Revenue": info.get('totalRevenue'),
                "Net Income": info.get('netIncomeToCommon'),
                "Total Cash": info.get('totalCash'),
                "Total Debt/Equity": info.get('debtToEquity'),
                "Operating Cash Flow": info.get('operatingCashflow'),
                "Levered Free Cash Flow": info.get('freeCashflow')
            }
            
            return {
                'valuation_measures': valuation_measures,
                'financial_highlights': financial_highlights,
                'financials': financials,
                'balance_sheet': balance_sheet,
                'cashflow': cashflow
            }
            
        except Exception as e:
            print(f"Error fetching detailed data for {ticker_code}: {str(e)}")
            return None

    def debug_ticker_info(self, ticker_code: str) -> None:
        """Debug function to print all available info from yfinance"""
        try:
            ticker = yf.Ticker(f"{ticker_code}.SA")
            
            print(f"\n=== Debug Info for {ticker_code} ===")
            
            # Get all info
            info = ticker.info
            print("\nAvailable fields in info:")
            for key, value in info.items():
                print(f"{key}: {value}")
            
            # Get financials
            print("\nFinancials:")
            print(ticker.financials)
            
            # Get balance sheet
            print("\nBalance Sheet:")
            print(ticker.balance_sheet)
            
            # Get cashflow
            print("\nCash Flow:")
            print(ticker.cashflow)
            
            # Get dividends
            print("\nDividends:")
            print(ticker.dividends)
            
            # Get actions (dividends and splits)
            print("\nActions:")
            print(ticker.actions)
            
            return info
            
        except Exception as e:
            print(f"Error fetching debug data: {str(e)}")
            return None 