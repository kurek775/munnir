#pragma once

#include <cstdint>

namespace munnir {

// ── Risk Tolerance ──────────────────────────────────────────────────
//
// Think of risk tolerance like a speed dial on a car:
//   Low    = city driving  (cautious, small bets)
//   Medium = highway       (moderate speed, moderate bets)
//   High   = track day     (aggressive, large bets)
//
// Each level maps to a base percentage of your balance that you're
// willing to risk on a single trade.

enum class RiskTolerance { Low, Medium, High };

// Returns the base risk percentage for a given tolerance level.
//   Low    -> 0.01 (1%)
//   Medium -> 0.03 (3%)
//   High   -> 0.05 (5%)
[[nodiscard]] double risk_percentage(RiskTolerance tolerance);

// ── Dynamic Risk Adjustment ─────────────────────────────────────────
//
// Imagine your balance is like a fuel tank. If you're running low
// (drawdown), you drive more carefully. If you've topped up (gains),
// you can push a little harder — but not recklessly.
//
// Formula:
//   ratio = current_balance / original_balance
//   if ratio < 1.0 (drawdown): scale linearly (e.g. 50% balance = 50% risk)
//   if ratio >= 1.0 (gains):   scale modestly, capped at 1.5x base risk
//
// Returns the adjusted risk percentage (e.g. 0.015 for 1.5%).
[[nodiscard]] double adjust_risk(int64_t current_balance_cents,
                   int64_t original_balance_cents,
                   RiskTolerance tolerance);

} // namespace munnir
