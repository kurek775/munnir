#pragma once

#include <cstdint>

namespace munnir {

// ── Profit & Loss ───────────────────────────────────────────────────
//
// P&L is just "what did I make (or lose)?"
//
// Think of it like buying apples:
//   You bought 10 apples at $2 each ($20 total).
//   Now they're $3 each ($30 total).
//   Your P&L = $30 - $20 = +$10 profit.
//
// We work in cents to avoid floating-point money bugs.

// Returns absolute P&L in cents.
//   pnl = (current_price - entry_price) * quantity
[[nodiscard]] int64_t calculate_pnl(int64_t entry_price_cents,
                      int64_t current_price_cents,
                      int64_t quantity);

// Returns P&L as a ratio (e.g. 0.25 = 25% gain, -0.10 = 10% loss).
//   pnl_pct = (current_price - entry_price) / entry_price
// Returns 0.0 if entry_price is zero (avoids division by zero).
[[nodiscard]] double calculate_pnl_percentage(int64_t entry_price_cents,
                                int64_t current_price_cents);

} // namespace munnir
