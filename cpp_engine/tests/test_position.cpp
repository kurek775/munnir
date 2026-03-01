#include <catch2/catch_test_macros.hpp>
#include "munnir_engine/position.hpp"

TEST_CASE("calculate_position basic case", "[position]") {
    // $1,000 balance, Medium risk (3%), full conviction, $10/share.
    // risk_amount = 100,000 * 0.03 * 1.0 = 3,000 cents.
    // shares = floor(3000 / 1000) = 3.
    REQUIRE(munnir::calculate_position(100'000,
                                       munnir::RiskTolerance::Medium,
                                       1.0, 1000) == 3);
}

TEST_CASE("calculate_position with partial conviction", "[position]") {
    // $1,000 balance, Medium risk (3%), 50% conviction, $10/share.
    // risk_amount = 100,000 * 0.03 * 0.5 = 1,500 cents.
    // shares = floor(1500 / 1000) = 1.
    REQUIRE(munnir::calculate_position(100'000,
                                       munnir::RiskTolerance::Medium,
                                       0.5, 1000) == 1);
}

TEST_CASE("calculate_position returns 0 for zero balance", "[position]") {
    REQUIRE(munnir::calculate_position(0, munnir::RiskTolerance::High,
                                       1.0, 1000) == 0);
}

TEST_CASE("calculate_position returns 0 for zero price", "[position]") {
    REQUIRE(munnir::calculate_position(100'000,
                                       munnir::RiskTolerance::High,
                                       1.0, 0) == 0);
}

TEST_CASE("calculate_position returns 0 for negative balance", "[position]") {
    REQUIRE(munnir::calculate_position(-50'000,
                                       munnir::RiskTolerance::Medium,
                                       1.0, 1000) == 0);
}

TEST_CASE("calculate_position clamps conviction above 1.0", "[position]") {
    // conviction=1.5 clamped to 1.0 → same as full conviction.
    REQUIRE(munnir::calculate_position(100'000,
                                       munnir::RiskTolerance::Medium,
                                       1.5, 1000) == 3);
}

TEST_CASE("calculate_position floors to whole shares", "[position]") {
    // $1,000 balance, Low risk (1%), full conviction, $3/share.
    // risk_amount = 100,000 * 0.01 * 1.0 = 1,000 cents.
    // shares = floor(1000 / 300) = floor(3.333) = 3.
    REQUIRE(munnir::calculate_position(100'000,
                                       munnir::RiskTolerance::Low,
                                       1.0, 300) == 3);
}

TEST_CASE("calculate_position with explicit risk_pct", "[position]") {
    // Same as basic case but using the double overload.
    // $1,000 balance, 3% risk, full conviction, $10/share → 3 shares.
    REQUIRE(munnir::calculate_position(100'000, 0.03, 1.0, 1000) == 3);
}
