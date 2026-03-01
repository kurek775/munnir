#include <catch2/catch_test_macros.hpp>
#include "munnir_engine/hello.hpp"

TEST_CASE("add returns the sum of two integers", "[math]") {
    REQUIRE(munnir::add(40, 2) == 42);
    REQUIRE(munnir::add(0, 0) == 0);
    REQUIRE(munnir::add(-1, 1) == 0);
    REQUIRE(munnir::add(-5, -3) == -8);
}
