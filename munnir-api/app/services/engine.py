"""Interface to the C++ munnir_engine.

Falls back to a pure-Python implementation when the compiled module is not
available (e.g. during early development or CI without a C++ build).
"""

import enum
import logging
import math

logger = logging.getLogger(__name__)

_HAS_CPP = False

try:
    import munnir_engine as _engine  # type: ignore[import-untyped]

    _HAS_CPP = True
    logger.info("Using C++ munnir_engine")
except ImportError:
    logger.warning("C++ munnir_engine not found — using Python fallback")


# ── Risk Tolerance Enum ──────────────────────────────────────────────

class RiskTolerance(enum.Enum):
    """Maps to DB string values and C++ RiskTolerance enum."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


_RISK_PERCENTAGES = {
    RiskTolerance.LOW: 0.01,
    RiskTolerance.MEDIUM: 0.03,
    RiskTolerance.HIGH: 0.05,
}

_MAX_GAIN_MULTIPLIER = 1.5

# Map Python enum → C++ enum.
if _HAS_CPP:
    _PY_TO_CPP_RISK = {
        RiskTolerance.LOW: _engine.RiskTolerance.Low,
        RiskTolerance.MEDIUM: _engine.RiskTolerance.Medium,
        RiskTolerance.HIGH: _engine.RiskTolerance.High,
    }


# ── Hello (pipeline health check) ───────────────────────────────────

def add(a: int, b: int) -> int:
    if _HAS_CPP:
        return _engine.add(a, b)
    return a + b


# ── Risk ─────────────────────────────────────────────────────────────

def risk_percentage(tolerance: RiskTolerance) -> float:
    """Base risk percentage for a tolerance level."""
    if _HAS_CPP:
        return _engine.risk_percentage(_PY_TO_CPP_RISK[tolerance])
    return _RISK_PERCENTAGES[tolerance]


def adjust_risk(
    current_balance_cents: int,
    original_balance_cents: int,
    tolerance: RiskTolerance,
) -> float:
    """Dynamically adjust risk based on balance changes."""
    if _HAS_CPP:
        return _engine.adjust_risk(
            current_balance_cents,
            original_balance_cents,
            _PY_TO_CPP_RISK[tolerance],
        )

    # Pure-Python fallback (mirrors C++ logic exactly).
    base = _RISK_PERCENTAGES[tolerance]

    if original_balance_cents <= 0:
        return base

    ratio = current_balance_cents / original_balance_cents

    if ratio < 1.0:
        return base * max(0.0, ratio)

    gain_multiplier = 1.0 + (ratio - 1.0) * 0.5
    gain_multiplier = min(gain_multiplier, _MAX_GAIN_MULTIPLIER)
    return base * gain_multiplier


# ── P&L ──────────────────────────────────────────────────────────────

def calculate_pnl(
    entry_price_cents: int,
    current_price_cents: int,
    quantity: int,
) -> int:
    """Absolute P&L in cents."""
    if _HAS_CPP:
        return _engine.calculate_pnl(
            entry_price_cents, current_price_cents, quantity,
        )
    return (current_price_cents - entry_price_cents) * quantity


def calculate_pnl_percentage(
    entry_price_cents: int,
    current_price_cents: int,
) -> float:
    """P&L as a ratio (e.g. 0.25 = 25% gain)."""
    if _HAS_CPP:
        return _engine.calculate_pnl_percentage(
            entry_price_cents, current_price_cents,
        )
    if entry_price_cents == 0:
        return 0.0
    return (current_price_cents - entry_price_cents) / entry_price_cents


# ── Position Sizing ──────────────────────────────────────────────────

def calculate_position(
    balance_cents: int,
    tolerance: RiskTolerance,
    conviction: float,
    asset_price_cents: int,
) -> int:
    """Number of whole shares to buy (enum risk tolerance)."""
    if _HAS_CPP:
        return _engine.calculate_position(
            balance_cents,
            _PY_TO_CPP_RISK[tolerance],
            conviction,
            asset_price_cents,
        )

    # Pure-Python fallback.
    if balance_cents <= 0 or asset_price_cents <= 0:
        return 0

    conviction = max(0.0, min(1.0, conviction))
    risk_pct = _RISK_PERCENTAGES[tolerance]
    risk_amount = balance_cents * risk_pct * conviction
    return max(0, math.floor(risk_amount / asset_price_cents))
