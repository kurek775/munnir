#include <catch2/catch_test_macros.hpp>
#include <catch2/matchers/catch_matchers_floating_point.hpp>
#include "munnir_engine/risk.hpp"

using Catch::Matchers::WithinAbs;

TEST_CASE("risk_percentage returns correct base percentages", "[risk]") {
    REQUIRE_THAT(munnir::risk_percentage(munnir::RiskTolerance::Low),
                 WithinAbs(0.01, 1e-9));
    REQUIRE_THAT(munnir::risk_percentage(munnir::RiskTolerance::Medium),
                 WithinAbs(0.03, 1e-9));
    REQUIRE_THAT(munnir::risk_percentage(munnir::RiskTolerance::High),
                 WithinAbs(0.05, 1e-9));
}

TEST_CASE("adjust_risk scales down on drawdown", "[risk]") {
    // Lost half: 50,000 of 100,000 → risk should be halved.
    double adjusted = munnir::adjust_risk(50'000, 100'000,
                                          munnir::RiskTolerance::Medium);
    REQUIRE_THAT(adjusted, WithinAbs(0.015, 1e-9));  // 3% * 0.5
}

TEST_CASE("adjust_risk returns base when balance unchanged", "[risk]") {
    double adjusted = munnir::adjust_risk(100'000, 100'000,
                                          munnir::RiskTolerance::Medium);
    REQUIRE_THAT(adjusted, WithinAbs(0.03, 1e-9));
}

TEST_CASE("adjust_risk scales up modestly on gains", "[risk]") {
    // Gained 20%: 120,000 of 100,000 → multiplier = 1 + 0.2*0.5 = 1.10
    double adjusted = munnir::adjust_risk(120'000, 100'000,
                                          munnir::RiskTolerance::Medium);
    REQUIRE_THAT(adjusted, WithinAbs(0.033, 1e-9));  // 3% * 1.10
}

TEST_CASE("adjust_risk caps gain multiplier at 1.5x", "[risk]") {
    // Tripled: 300,000 of 100,000 → multiplier would be 1 + 2.0*0.5 = 2.0
    // but capped at 1.5.
    double adjusted = munnir::adjust_risk(300'000, 100'000,
                                          munnir::RiskTolerance::High);
    REQUIRE_THAT(adjusted, WithinAbs(0.075, 1e-9));  // 5% * 1.5
}

TEST_CASE("adjust_risk handles zero and negative original balance", "[risk]") {
    // Zero original → returns base risk.
    REQUIRE_THAT(munnir::adjust_risk(50'000, 0, munnir::RiskTolerance::Low),
                 WithinAbs(0.01, 1e-9));
    // Negative original → returns base risk.
    REQUIRE_THAT(munnir::adjust_risk(50'000, -100, munnir::RiskTolerance::Low),
                 WithinAbs(0.01, 1e-9));
    // Zero current balance → zero risk.
    REQUIRE_THAT(munnir::adjust_risk(0, 100'000, munnir::RiskTolerance::Medium),
                 WithinAbs(0.0, 1e-9));
}
