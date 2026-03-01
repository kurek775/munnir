"""Tests for the engine service layer.

These assertions work whether the C++ engine or the Python fallback is active.
"""

import math

import pytest

from app.services.engine import (
    RiskTolerance,
    adjust_risk,
    calculate_pnl,
    calculate_pnl_percentage,
    calculate_position,
    risk_percentage,
)


class TestRiskPercentage:
    def test_low(self):
        assert risk_percentage(RiskTolerance.LOW) == pytest.approx(0.01)

    def test_medium(self):
        assert risk_percentage(RiskTolerance.MEDIUM) == pytest.approx(0.03)

    def test_high(self):
        assert risk_percentage(RiskTolerance.HIGH) == pytest.approx(0.05)


class TestAdjustRisk:
    def test_drawdown_halves_risk(self):
        # Lost half: 50k of 100k → risk halved.
        result = adjust_risk(50_000, 100_000, RiskTolerance.MEDIUM)
        assert result == pytest.approx(0.015)

    def test_unchanged_balance(self):
        result = adjust_risk(100_000, 100_000, RiskTolerance.MEDIUM)
        assert result == pytest.approx(0.03)

    def test_modest_gain(self):
        # 120% balance → multiplier = 1 + 0.2*0.5 = 1.10
        result = adjust_risk(120_000, 100_000, RiskTolerance.MEDIUM)
        assert result == pytest.approx(0.033)

    def test_gain_cap(self):
        # 3x balance → capped at 1.5x.
        result = adjust_risk(300_000, 100_000, RiskTolerance.HIGH)
        assert result == pytest.approx(0.075)

    def test_zero_original_balance(self):
        result = adjust_risk(50_000, 0, RiskTolerance.LOW)
        assert result == pytest.approx(0.01)

    def test_zero_current_balance(self):
        result = adjust_risk(0, 100_000, RiskTolerance.MEDIUM)
        assert result == pytest.approx(0.0)


class TestCalculatePosition:
    def test_basic(self):
        # $1,000 balance, Medium (3%), full conviction, $10/share → 3.
        assert calculate_position(100_000, RiskTolerance.MEDIUM, 1.0, 1000) == 3

    def test_partial_conviction(self):
        # $1,000, Medium (3%), 50% conviction, $10/share → 1.
        assert calculate_position(100_000, RiskTolerance.MEDIUM, 0.5, 1000) == 1

    def test_zero_balance(self):
        assert calculate_position(0, RiskTolerance.HIGH, 1.0, 1000) == 0

    def test_zero_price(self):
        assert calculate_position(100_000, RiskTolerance.HIGH, 1.0, 0) == 0

    def test_negative_balance(self):
        assert calculate_position(-50_000, RiskTolerance.MEDIUM, 1.0, 1000) == 0

    def test_clamps_conviction_above_one(self):
        # conviction=1.5 clamped to 1.0 → same as full conviction.
        assert calculate_position(100_000, RiskTolerance.MEDIUM, 1.5, 1000) == 3

    def test_floors_to_whole_shares(self):
        # $1,000, Low (1%), full conviction, $3/share.
        # risk = 1000 cents, shares = floor(1000/300) = 3.
        assert calculate_position(100_000, RiskTolerance.LOW, 1.0, 300) == 3

    def test_low_risk_high_price(self):
        # $1,000, Low (1%), full conviction, $20/share.
        # risk = 1000 cents, shares = floor(1000/2000) = 0.
        assert calculate_position(100_000, RiskTolerance.LOW, 1.0, 2000) == 0


class TestCalculatePnl:
    def test_profit(self):
        assert calculate_pnl(1000, 1200, 5) == 1000

    def test_loss(self):
        assert calculate_pnl(1000, 800, 5) == -1000

    def test_no_change(self):
        assert calculate_pnl(1000, 1000, 10) == 0

    def test_zero_quantity(self):
        assert calculate_pnl(1000, 2000, 0) == 0

    def test_large_values(self):
        assert calculate_pnl(100_000_000, 100_000_100, 1_000_000) == 100_000_000


class TestCalculatePnlPercentage:
    def test_gain(self):
        assert calculate_pnl_percentage(1000, 1200) == pytest.approx(0.2)

    def test_loss(self):
        assert calculate_pnl_percentage(1000, 800) == pytest.approx(-0.2)

    def test_no_change(self):
        assert calculate_pnl_percentage(1000, 1000) == pytest.approx(0.0)

    def test_zero_entry_price(self):
        assert calculate_pnl_percentage(0, 1000) == pytest.approx(0.0)
