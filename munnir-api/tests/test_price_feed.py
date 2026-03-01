"""Tests for price feed service (mocked yfinance)."""

from unittest.mock import MagicMock, patch

import pytest

from app.services.price_feed import PriceFeedError, get_price_cents


@pytest.mark.asyncio
async def test_valid_ticker_returns_cents():
    """Valid ticker returns price as integer cents."""
    mock_ticker = MagicMock()
    mock_ticker.fast_info.last_price = 150.25

    with patch("app.services.price_feed.yf.Ticker", return_value=mock_ticker):
        result = await get_price_cents("AAPL")
    assert result == 15025
    assert isinstance(result, int)


@pytest.mark.asyncio
async def test_invalid_ticker_raises_error():
    """Invalid ticker (None price) raises PriceFeedError."""
    mock_ticker = MagicMock()
    mock_ticker.fast_info.last_price = None

    with patch("app.services.price_feed.yf.Ticker", return_value=mock_ticker):
        with pytest.raises(PriceFeedError, match="No valid price"):
            await get_price_cents("XXXYZ")


@pytest.mark.asyncio
async def test_yfinance_exception_raises_error():
    """yfinance exception is wrapped in PriceFeedError."""
    with patch(
        "app.services.price_feed.yf.Ticker",
        side_effect=Exception("Network error"),
    ):
        with pytest.raises(PriceFeedError, match="Failed to fetch"):
            await get_price_cents("AAPL")


@pytest.mark.asyncio
async def test_result_is_integer():
    """Price cents should always be an integer."""
    mock_ticker = MagicMock()
    mock_ticker.fast_info.last_price = 99.999

    with patch("app.services.price_feed.yf.Ticker", return_value=mock_ticker):
        result = await get_price_cents("TSLA")
    assert isinstance(result, int)
    assert result == 10000  # 99.999 rounds to 100.00 = 10000 cents
