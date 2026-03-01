import pytest
from pydantic import ValidationError

from app.schemas.trade_signal import TradeSignalLLM


class TestTradeSignalLLM:
    def _valid_data(self, **overrides):
        base = {
            "action": "BUY",
            "asset": "AAPL",
            "conviction": 0.8,
            "reasoning": "Strong earnings report suggests continued growth",
            "risk_score": 5,
        }
        base.update(overrides)
        return base

    def test_valid_buy(self):
        signal = TradeSignalLLM(**self._valid_data())
        assert signal.action == "BUY"
        assert signal.asset == "AAPL"

    def test_valid_sell(self):
        signal = TradeSignalLLM(**self._valid_data(action="SELL"))
        assert signal.action == "SELL"

    def test_valid_hold(self):
        signal = TradeSignalLLM(**self._valid_data(action="HOLD", asset="CASH"))
        assert signal.action == "HOLD"

    def test_invalid_action(self):
        with pytest.raises(ValidationError):
            TradeSignalLLM(**self._valid_data(action="WAIT"))

    def test_lowercase_asset_rejected(self):
        with pytest.raises(ValidationError):
            TradeSignalLLM(**self._valid_data(asset="aapl"))

    def test_asset_too_long(self):
        with pytest.raises(ValidationError):
            TradeSignalLLM(**self._valid_data(asset="TOOLONG"))

    def test_conviction_zero(self):
        signal = TradeSignalLLM(**self._valid_data(conviction=0.0))
        assert signal.conviction == 0.0

    def test_conviction_one(self):
        signal = TradeSignalLLM(**self._valid_data(conviction=1.0))
        assert signal.conviction == 1.0

    def test_conviction_below_zero(self):
        with pytest.raises(ValidationError):
            TradeSignalLLM(**self._valid_data(conviction=-0.1))

    def test_conviction_above_one(self):
        with pytest.raises(ValidationError):
            TradeSignalLLM(**self._valid_data(conviction=1.1))

    def test_reasoning_too_short(self):
        with pytest.raises(ValidationError):
            TradeSignalLLM(**self._valid_data(reasoning="Short"))

    def test_reasoning_max_length(self):
        signal = TradeSignalLLM(**self._valid_data(reasoning="A" * 500))
        assert len(signal.reasoning) == 500

    def test_reasoning_too_long(self):
        with pytest.raises(ValidationError):
            TradeSignalLLM(**self._valid_data(reasoning="A" * 501))

    def test_risk_score_min(self):
        signal = TradeSignalLLM(**self._valid_data(risk_score=1))
        assert signal.risk_score == 1

    def test_risk_score_max(self):
        signal = TradeSignalLLM(**self._valid_data(risk_score=10))
        assert signal.risk_score == 10

    def test_risk_score_below_min(self):
        with pytest.raises(ValidationError):
            TradeSignalLLM(**self._valid_data(risk_score=0))

    def test_risk_score_above_max(self):
        with pytest.raises(ValidationError):
            TradeSignalLLM(**self._valid_data(risk_score=11))
