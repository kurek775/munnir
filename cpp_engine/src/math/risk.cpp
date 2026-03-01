#include "munnir_engine/risk.hpp"

#include <algorithm>

namespace munnir {

// Base risk percentages — how much of your balance you risk per trade.
static constexpr double kRiskLow    = 0.01;  // 1%
static constexpr double kRiskMedium = 0.03;  // 3%
static constexpr double kRiskHigh   = 0.05;  // 5%

// Maximum multiplier for gains — even if you've doubled your money,
// never risk more than 1.5x the base percentage.
static constexpr double kMaxGainMultiplier = 1.5;

double risk_percentage(RiskTolerance tolerance) {
    switch (tolerance) {
        case RiskTolerance::Low:    return kRiskLow;
        case RiskTolerance::Medium: return kRiskMedium;
        case RiskTolerance::High:   return kRiskHigh;
    }
    return kRiskMedium;  // unreachable, but satisfies compilers
}

double adjust_risk(int64_t current_balance_cents,
                   int64_t original_balance_cents,
                   RiskTolerance tolerance) {
    double base = risk_percentage(tolerance);

    // Guard: if original balance is zero or negative, just return base.
    if (original_balance_cents <= 0) {
        return base;
    }

    double ratio = static_cast<double>(current_balance_cents)
                 / static_cast<double>(original_balance_cents);

    // Drawdown: scale linearly. If you lost half, risk half.
    // Zero or negative balance → zero risk.
    if (ratio < 1.0) {
        return base * std::max(0.0, ratio);
    }

    // Gains: modest scaling, capped at 1.5x.
    // Example: 120% balance → 1 + (0.2 * 0.5) = 1.10x multiplier.
    double gain_multiplier = 1.0 + (ratio - 1.0) * 0.5;
    gain_multiplier = std::min(gain_multiplier, kMaxGainMultiplier);

    return base * gain_multiplier;
}

} // namespace munnir
