import requests
from config import COINGECKO_API_KEY, COINGECKO_API_BASE_URL


class CoinGeckoAPI:
    def __init__(self):
        self.base_url = COINGECKO_API_BASE_URL
        self.headers = {
            "x-cg-demo-api-key": COINGECKO_API_KEY,
            "Content-Type": "application/json",
        }

    def _make_request(self, endpoint: str, params: dict = None) -> dict:
        """Make a request to the CoinGecko API with proper error handling."""
        try:
            response = requests.get(
                f"{self.base_url}/{endpoint}", headers=self.headers, params=params
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            # Log error and raise custom exception
            raise Exception(f"CoinGecko API error: {str(e)}")

    def get_coin_data(self, coin_id: str) -> dict:
        """Get detailed data for a specific coin."""
        return self._make_request(
            f"coins/{coin_id}",
            {
                "localization": "false",
                "tickers": "false",
                "community_data": "false",
                "developer_data": "false",
            },
        )

    def search_coins(self, query: str) -> dict:
        """Search for coins by name or symbol."""
        return self._make_request("search", {"query": query})

    def get_market_chart(
        self, coin_id: str, vs_currency: str = "usd", days: int = 1
    ) -> dict:
        """Get market chart data for a coin."""
        return self._make_request(
            f"coins/{coin_id}/market_chart",
            {
                "vs_currency": vs_currency,
                "days": days,
                "interval": "daily" if days > 90 else "hourly",
            },
        )
