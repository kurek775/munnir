"""Tests for slippage simulation."""

from unittest.mock import patch

from app.services.slippage import SlippageResult, apply_slippage


def test_buy_increases_price():
    """BUY slippage should always result in higher price."""
    with patch("app.services.slippage.random.uniform", return_value=0.005):
        result = apply_slippage(10000, "BUY", "medium", True)
    assert result.execution_price_cents > 10000


def test_sell_decreases_price():
    """SELL slippage should always result in lower price."""
    with patch("app.services.slippage.random.uniform", return_value=0.005):
        result = apply_slippage(10000, "SELL", "medium", True)
    assert result.execution_price_cents < 10000


def test_disabled_returns_exact_price():
    """When disabled, execution price equals market price."""
    result = apply_slippage(10000, "BUY", "medium", False)
    assert result.execution_price_cents == 10000
    assert result.factor == 0.0


def test_low_tolerance_range():
    """Low tolerance slippage factor should be in 0.1%-0.3% range."""
    with patch("app.services.slippage.random.uniform", return_value=0.002) as mock_uniform:
        apply_slippage(10000, "BUY", "low", True)
    mock_uniform.assert_called_once_with(0.001, 0.003)


def test_high_tolerance_range():
    """High tolerance slippage factor should be in 0.8%-2.0% range."""
    with patch("app.services.slippage.random.uniform", return_value=0.01) as mock_uniform:
        apply_slippage(10000, "BUY", "high", True)
    mock_uniform.assert_called_once_with(0.008, 0.020)


def test_buy_slippage_always_unfavorable():
    """BUY slippage factor should produce execution_price >= market_price."""
    for _ in range(50):
        result = apply_slippage(10000, "BUY", "medium", True)
        assert result.execution_price_cents >= 10000
        assert result.factor > 0


def test_sell_slippage_always_unfavorable():
    """SELL slippage factor should produce execution_price <= market_price."""
    for _ in range(50):
        result = apply_slippage(10000, "SELL", "medium", True)
        assert result.execution_price_cents <= 10000
        assert result.factor > 0
