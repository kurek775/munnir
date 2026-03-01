#include "munnir_engine/position.hpp"

#include <algorithm>
#include <cmath>

namespace munnir {

int64_t calculate_position(int64_t balance_cents,
                           double risk_pct,
                           double conviction,
                           int64_t asset_price_cents) {
    // Guard: can't buy anything with zero/negative balance or price.
    if (balance_cents <= 0 || asset_price_cents <= 0) {
        return 0;
    }

    // Clamp conviction to [0.0, 1.0].
    conviction = std::clamp(conviction, 0.0, 1.0);

    // Clamp risk_pct to non-negative.
    risk_pct = std::max(0.0, risk_pct);

    // risk_amount = balance * risk_pct * conviction  (all in cents)
    double risk_amount = static_cast<double>(balance_cents) * risk_pct * conviction;

    // Floor-divide: whole shares only, you can't buy half a share.
    auto shares = static_cast<int64_t>(std::floor(risk_amount
                / static_cast<double>(asset_price_cents)));

    return std::max(int64_t{0}, shares);
}

int64_t calculate_position(int64_t balance_cents,
                           RiskTolerance tolerance,
                           double conviction,
                           int64_t asset_price_cents) {
    return calculate_position(balance_cents,
                              risk_percentage(tolerance),
                              conviction,
                              asset_price_cents);
}

} // namespace munnir
