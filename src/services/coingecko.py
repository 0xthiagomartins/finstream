import requests
import time
from config import COINGECKO_API_BASE_URL
from .cache_manager import CacheManager
from concurrent.futures import ThreadPoolExecutor


class CoinGeckoAPI:
    def __init__(self):
        self.base_url = COINGECKO_API_BASE_URL
        self.headers = {
            "Content-Type": "application/json",
        }
        self.cache = CacheManager(max_size=100, ttl=300)  # 5 minutes TTL
        self.executor = ThreadPoolExecutor(max_workers=3)

    def _make_request(self, endpoint: str, params: dict = None, max_retries: int = 3) -> dict:
        """Make a request to the CoinGecko API with retry logic."""
        for attempt in range(max_retries):
            try:
                response = requests.get(
                    f"{self.base_url}/{endpoint}",
                    params=params,
                    timeout=30
                )
                
                if response.status_code == 429:  # Rate limit hit
                    wait_time = 2 ** attempt * 30  # Exponential backoff
                    time.sleep(wait_time)
                    continue
                    
                response.raise_for_status()
                return response.json()
                
            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:  # Last attempt
                    if hasattr(e, 'response') and e.response.status_code == 429:
                        raise Exception("Rate limit exceeded. Please try again in a few minutes.")
                    raise Exception(f"CoinGecko API error: {str(e)}")
                time.sleep(2 ** attempt * 30)  # Exponential backoff before retry

    def get_coin_data(self, coin_id: str) -> dict:
        """Get detailed data for a specific coin with caching."""
        cache_key = f"coin_data:{coin_id}"
        return self.cache.get_or_set(
            cache_key,
            lambda: self._make_request(
                f"coins/{coin_id}",
                {
                    "localization": "false",
                    "tickers": "false",
                    "community_data": "false",
                    "developer_data": "false",
                },
            )
        )

    def search_coins(self, query: str) -> dict:
        """Search for coins by name or symbol."""
        time.sleep(6)  # Add delay between requests
        return self._make_request("search", {"query": query})

    def get_market_chart(
        self, coin_id: str, vs_currency: str = "usd", days: int = 1
    ) -> dict:
        """Get market chart data for a coin with caching."""
        cache_key = f"market_chart:{coin_id}:{vs_currency}:{days}"
        return self.cache.get_or_set(
            cache_key,
            lambda: self._make_request(
                f"coins/{coin_id}/market_chart",
                params={
                    "vs_currency": vs_currency,
                    "days": days,
                    "interval": "daily"
                }
            )
        )

    def batch_get_market_charts(self, coin_ids: list, vs_currency: str = "usd", days: int = 1) -> dict:
        """Get market chart data for multiple coins in parallel."""
        def fetch_single(coin_id):
            try:
                return coin_id, self.get_market_chart(coin_id, vs_currency, days)
            except Exception as e:
                return coin_id, None

        # Use ThreadPoolExecutor for parallel requests
        results = {}
        futures = [
            self.executor.submit(fetch_single, coin_id)
            for coin_id in coin_ids
        ]
        
        for future in futures:
            coin_id, data = future.result()
            if data:
                results[coin_id] = data
                
        return results
