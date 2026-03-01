"""Price feed service — fetches live prices via yfinance."""

import asyncio
import logging

import yfinance as yf

logger = logging.getLogger(__name__)


class PriceFeedError(Exception):
    """Raised when a price cannot be fetched."""


def _fetch_price_sync(ticker: str) -> float:
    """Synchronous yfinance call — runs in a thread."""
    try:
        t = yf.Ticker(ticker)
        price = t.fast_info.last_price
    except Exception as exc:
        raise PriceFeedError(f"Failed to fetch price for {ticker}: {exc}") from exc

    if price is None or price <= 0:
        raise PriceFeedError(f"No valid price for {ticker}")
    return float(price)


async def get_price_cents(ticker: str) -> int:
    """Fetch the current market price in cents (async wrapper)."""
    price = await asyncio.to_thread(_fetch_price_sync, ticker)
    return int(round(price * 100))
