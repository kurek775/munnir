"""Slippage simulation per risk tolerance."""

import random
from dataclasses import dataclass

# Slippage ranges by risk tolerance (min%, max%)
_SLIPPAGE_RANGES = {
    "low": (0.001, 0.003),       # 0.1% – 0.3%
    "medium": (0.003, 0.008),    # 0.3% – 0.8%
    "high": (0.008, 0.020),      # 0.8% – 2.0%
}


@dataclass(frozen=True)
class SlippageResult:
    execution_price_cents: int
    factor: float


def apply_slippage(
    market_price_cents: int,
    side: str,
    tolerance: str = "medium",
    enabled: bool = True,
) -> SlippageResult:
    """Apply simulated slippage to a market price.

    Slippage is always unfavorable: BUY pays more, SELL receives less.
    """
    if not enabled:
        return SlippageResult(
            execution_price_cents=market_price_cents,
            factor=0.0,
        )

    min_pct, max_pct = _SLIPPAGE_RANGES.get(tolerance, _SLIPPAGE_RANGES["medium"])
    factor = random.uniform(min_pct, max_pct)

    # BUY: price goes up (+1), SELL: price goes down (-1)
    direction = 1 if side == "BUY" else -1
    exec_price = market_price_cents * (1 + factor * direction)
    exec_price_cents = int(round(exec_price))

    return SlippageResult(
        execution_price_cents=exec_price_cents,
        factor=factor,
    )
