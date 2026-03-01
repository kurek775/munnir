#pragma once

#include <cstdint>
#include "munnir_engine/risk.hpp"

namespace munnir {

// ── Position Sizing ─────────────────────────────────────────────────
//
// "How many shares should I buy?" is the core question.
//
// Imagine you have $1,000 and you're willing to risk 3% ($30) on a
// trade. If you're 80% confident in the trade, you'd risk
// $30 * 0.80 = $24. If each share costs $10, you can buy
// floor($24 / $10) = 2 shares.
//
// Formula:
//   risk_amount = balance * risk_pct * conviction
//   shares = floor(risk_amount / asset_price)
//
// All money values are in cents. Conviction is 0.0–1.0 (clamped).

// Uses the enum-based risk tolerance to determine risk percentage.
// Returns number of whole shares to buy (always >= 0).
[[nodiscard]] int64_t calculate_position(int64_t balance_cents,
                                         RiskTolerance tolerance,
                                         double conviction,
                                         int64_t asset_price_cents);

// Uses an explicit risk percentage (e.g. 0.03 for 3%).
// Returns number of whole shares to buy (always >= 0).
[[nodiscard]] int64_t calculate_position(int64_t balance_cents,
                                         double risk_pct,
                                         double conviction,
                                         int64_t asset_price_cents);

} // namespace munnir
