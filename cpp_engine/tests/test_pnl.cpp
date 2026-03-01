#include <catch2/catch_test_macros.hpp>
#include <catch2/matchers/catch_matchers_floating_point.hpp>
#include "munnir_engine/pnl.hpp"

using Catch::Matchers::WithinAbs;

TEST_CASE("calculate_pnl shows profit", "[pnl]") {
    // Bought at $10.00 (1000 cents), now $12.00 (1200 cents), 5 shares.
    // PnL = (1200 - 1000) * 5 = 1000 cents = $10.00 profit.
    REQUIRE(munnir::calculate_pnl(1000, 1200, 5) == 1000);
}

TEST_CASE("calculate_pnl shows loss", "[pnl]") {
    // Bought at $10.00, now $8.00, 5 shares.
    // PnL = (800 - 1000) * 5 = -1000 cents = $10.00 loss.
    REQUIRE(munnir::calculate_pnl(1000, 800, 5) == -1000);
}

TEST_CASE("calculate_pnl is zero when price unchanged", "[pnl]") {
    REQUIRE(munnir::calculate_pnl(1000, 1000, 10) == 0);
}

TEST_CASE("calculate_pnl is zero when quantity is zero", "[pnl]") {
    REQUIRE(munnir::calculate_pnl(1000, 2000, 0) == 0);
}

TEST_CASE("calculate_pnl handles large values", "[pnl]") {
    // $1,000,000.00 entry, $1,000,001.00 current, 1,000,000 shares.
    // PnL = 100 * 1,000,000 = 100,000,000 cents = $1,000,000.
    int64_t entry   = 100'000'000;  // $1M in cents
    int64_t current = 100'000'100;  // $1M + $1 in cents
    int64_t qty     = 1'000'000;
    REQUIRE(munnir::calculate_pnl(entry, current, qty) == 100'000'000);
}

TEST_CASE("calculate_pnl_percentage shows gain", "[pnl]") {
    // $10 → $12 = 20% gain.
    REQUIRE_THAT(munnir::calculate_pnl_percentage(1000, 1200),
                 WithinAbs(0.2, 1e-9));
}

TEST_CASE("calculate_pnl_percentage shows loss", "[pnl]") {
    // $10 → $8 = 20% loss.
    REQUIRE_THAT(munnir::calculate_pnl_percentage(1000, 800),
                 WithinAbs(-0.2, 1e-9));
}

TEST_CASE("calculate_pnl_percentage is zero when price unchanged", "[pnl]") {
    REQUIRE_THAT(munnir::calculate_pnl_percentage(1000, 1000),
                 WithinAbs(0.0, 1e-9));
}

TEST_CASE("calculate_pnl_percentage returns 0 for zero entry price", "[pnl]") {
    REQUIRE_THAT(munnir::calculate_pnl_percentage(0, 1000),
                 WithinAbs(0.0, 1e-9));
}
