"""
prices.py — Fetch real-time prices from free APIs
Supports: yFinance (BR/US stocks), CoinGecko (crypto), AwesomeAPI (USD/BRL rate)
"""

from __future__ import annotations
import time
import requests
from dataclasses import dataclass
from typing import Optional
from functools import lru_cache


AWESOME_API = "https://economia.awesomeapi.com.br/json/last/USD-BRL"
COINGECKO_API = "https://api.coingecko.com/api/v3"
YFINANCE_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"


@dataclass
class PriceResult:
    symbol: str
    price: float
    currency: str
    source: str
    timestamp: float = 0.0

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = time.time()


class PriceFetcher:
    """Unified price fetcher with fallback strategies."""

    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": "dolar-flow/1.0"})

    # ------------------------------------------------------------------ #
    # USD/BRL exchange rate
    # ------------------------------------------------------------------ #

    def get_usd_brl(self) -> float:
        """Return current USD → BRL exchange rate."""
        try:
            r = self._session.get(AWESOME_API, timeout=self.timeout)
            r.raise_for_status()
            return float(r.json()["USDBRL"]["bid"])
        except Exception:
            # Hard fallback — will be stale, just avoids crash
            return 5.0

    # ------------------------------------------------------------------ #
    # Stocks via Yahoo Finance (no API key required)
    # ------------------------------------------------------------------ #

    def get_stock_price(self, symbol: str) -> Optional[PriceResult]:
        """
        Fetch stock price from Yahoo Finance.
        For B3 stocks, append .SA  (e.g. PETR4 → PETR4.SA)
        For US stocks, use raw ticker (e.g. AAPL)
        """
        url = YFINANCE_URL.format(symbol=symbol)
        try:
            r = self._session.get(url, timeout=self.timeout)
            r.raise_for_status()
            data = r.json()
            meta = data["chart"]["result"][0]["meta"]
            price = meta.get("regularMarketPrice") or meta.get("previousClose")
            currency = meta.get("currency", "USD")
            return PriceResult(symbol=symbol, price=float(price), currency=currency, source="yahoo")
        except Exception:
            return None

    # ------------------------------------------------------------------ #
    # Crypto via CoinGecko (free, no API key)
    # ------------------------------------------------------------------ #

    def get_crypto_price(self, coin_id: str, vs_currency: str = "usd") -> Optional[PriceResult]:
        """
        Fetch crypto price from CoinGecko.
        coin_id examples: 'bitcoin', 'ethereum', 'solana'
        """
        endpoint = f"{COINGECKO_API}/simple/price"
        params = {"ids": coin_id, "vs_currencies": vs_currency}
        try:
            r = self._session.get(endpoint, params=params, timeout=self.timeout)
            r.raise_for_status()
            price = r.json()[coin_id][vs_currency]
            return PriceResult(
                symbol=coin_id.upper(),
                price=float(price),
                currency=vs_currency.upper(),
                source="coingecko",
            )
        except Exception:
            return None

    def get_top_cryptos(self, n: int = 10, vs_currency: str = "usd") -> list[dict]:
        """Return top-N cryptos by market cap."""
        endpoint = f"{COINGECKO_API}/coins/markets"
        params = {
            "vs_currency": vs_currency,
            "order": "market_cap_desc",
            "per_page": n,
            "page": 1,
        }
        try:
            r = self._session.get(endpoint, params=params, timeout=self.timeout)
            r.raise_for_status()
            return r.json()
        except Exception:
            return []

    # ------------------------------------------------------------------ #
    # Batch fetch
    # ------------------------------------------------------------------ #

    def fetch_portfolio_prices(
        self, symbols_by_type: dict[str, list[str]]
    ) -> dict[str, Optional[PriceResult]]:
        """
        symbols_by_type: {
            'stock_br': ['PETR4.SA', 'VALE3.SA'],
            'stock_us': ['AAPL', 'MSFT'],
            'crypto':   ['bitcoin', 'ethereum'],
        }
        Returns symbol → PriceResult mapping.
        """
        results: dict[str, Optional[PriceResult]] = {}

        for symbol in symbols_by_type.get("stock_br", []):
            results[symbol] = self.get_stock_price(symbol)
            time.sleep(0.2)  # gentle rate limiting

        for symbol in symbols_by_type.get("stock_us", []):
            results[symbol] = self.get_stock_price(symbol)
            time.sleep(0.2)

        for coin_id in symbols_by_type.get("crypto", []):
            results[coin_id] = self.get_crypto_price(coin_id)
            time.sleep(0.3)

        return results
