---
name: cpp-engine
description: Use this skill whenever building, modifying, or debugging the Munnir C++ math engine — including risk calculations, portfolio optimization, market simulation, Monte Carlo methods, pybind11 bindings, CMake configuration, or Catch2 tests. Trigger when the user mentions C++ code in the engine, performance-critical math, NumPy/C++ data transfer, adding new computation modules, build errors, linker failures, segfaults, or anything under the cpp_engine directory. Also use when exposing new C++ functions to Python or debugging pybind11 type conversion issues.
---

# High-Performance Compute — Munnir C++ Engine

The C++ engine handles all numerically intensive work: risk scoring, portfolio optimization, Monte Carlo simulation, and pricing models. Python orchestrates; C++ computes.

## File Locations

| Purpose              | Path                                     |
| -------------------- | ---------------------------------------- |
| CMake config         | `cpp_engine/CMakeLists.txt`              |
| Public headers       | `cpp_engine/include/munnir_engine/`      |
| Math modules (src)   | `cpp_engine/src/math/`                   |
| Market simulation    | `cpp_engine/src/market/`                 |
| pybind11 bindings    | `cpp_engine/src/bindings.cpp`            |
| Catch2 tests         | `cpp_engine/tests/`                      |

## Stack

- **Standard**: C++20
- **Build**: CMake 3.20+
- **Python bindings**: pybind11
- **Testing**: Catch2 v3 (fetched via CMake FetchContent)
- **Linear algebra**: Eigen (optional, for matrix operations)

---

## Project Structure

```
cpp_engine/
├── CMakeLists.txt
├── include/munnir_engine/
│   ├── risk.hpp
│   ├── portfolio.hpp
│   └── simulation.hpp
├── src/
│   ├── math/
│   │   ├── risk.cpp
│   │   └── portfolio.cpp
│   ├── market/
│   │   └── simulation.cpp
│   └── bindings.cpp          # pybind11 — only file that touches Python
└── tests/
    ├── test_risk.cpp
    └── test_portfolio.cpp
```

The key rule: `bindings.cpp` is the **only** file that imports pybind11. All other `.cpp` files are pure C++ with no Python dependencies. This keeps the math testable in isolation.

---

## Adding a New Computation Module

Follow this sequence for every new piece of math added to the engine.

### 1. Write the header

Define the public interface in `cpp_engine/include/munnir_engine/`. Keep headers minimal — declarations only, no implementation:

```cpp
// include/munnir_engine/volatility.hpp
#pragma once

#include <vector>
#include <span>

namespace munnir {

struct VolatilityResult {
    double historical_vol;
    double annualized_vol;
    double max_drawdown;
};

// Compute volatility metrics from a price series.
// Prices must contain at least 2 elements.
[[nodiscard]] VolatilityResult compute_volatility(std::span<const double> prices);

} // namespace munnir
```

Use `std::span` for array parameters — it accepts both `std::vector` and raw buffers without copying. Use `[[nodiscard]]` on functions that return results to catch ignored return values at compile time.

### 2. Implement the source

Place implementation in the appropriate `src/` subdirectory:

```cpp
// src/math/volatility.cpp
#include "munnir_engine/volatility.hpp"

#include <cmath>
#include <algorithm>
#include <numeric>
#include <stdexcept>

namespace munnir {

VolatilityResult compute_volatility(std::span<const double> prices) {
    if (prices.size() < 2) {
        throw std::invalid_argument("Need at least 2 prices for volatility");
    }

    // Compute log returns
    std::vector<double> returns;
    returns.reserve(prices.size() - 1);
    for (size_t i = 1; i < prices.size(); ++i) {
        returns.push_back(std::log(prices[i] / prices[i - 1]));
    }

    // Historical volatility (std dev of returns)
    double mean = std::accumulate(returns.begin(), returns.end(), 0.0)
                  / static_cast<double>(returns.size());
    double sq_sum = std::accumulate(returns.begin(), returns.end(), 0.0,
        [mean](double acc, double r) { return acc + (r - mean) * (r - mean); });
    double hist_vol = std::sqrt(sq_sum / static_cast<double>(returns.size() - 1));

    // Annualized (assuming 252 trading days)
    double annual_vol = hist_vol * std::sqrt(252.0);

    // Max drawdown
    double peak = prices[0];
    double max_dd = 0.0;
    for (double p : prices) {
        peak = std::max(peak, p);
        max_dd = std::max(max_dd, (peak - p) / peak);
    }

    return {hist_vol, annual_vol, max_dd};
}

} // namespace munnir
```

Implementation guidelines:

- Throw `std::invalid_argument` for bad inputs — pybind11 converts these to Python `ValueError` automatically.
- Use `reserve()` on vectors when the size is known ahead of time.
- Avoid heap allocations in hot loops. Prefer stack-allocated or pre-allocated buffers.
- Use `static_cast` explicitly — never rely on implicit narrowing conversions.

### 3. Register the CMake target

Add the new source file to `cpp_engine/CMakeLists.txt`:

```cmake
add_library(munnir_engine_core STATIC
    src/math/risk.cpp
    src/math/portfolio.cpp
    src/math/volatility.cpp      # new
    src/market/simulation.cpp
)

target_include_directories(munnir_engine_core PUBLIC include)
target_compile_features(munnir_engine_core PUBLIC cxx_std_20)
```

The core library is a static lib with no pybind11 dependency. The pybind11 module links against it:

```cmake
pybind11_add_module(munnir_engine src/bindings.cpp)
target_link_libraries(munnir_engine PRIVATE munnir_engine_core)
```

### 4. Write Catch2 tests

One test file per module in `cpp_engine/tests/`:

```cpp
// tests/test_volatility.cpp
#include <catch2/catch_test_macros.hpp>
#include <catch2/matchers/catch_matchers_floating_point.hpp>
#include "munnir_engine/volatility.hpp"

using Catch::Matchers::WithinRel;

TEST_CASE("volatility of constant prices is zero", "[volatility]") {
    std::vector<double> flat = {100.0, 100.0, 100.0, 100.0};
    auto result = munnir::compute_volatility(flat);
    REQUIRE(result.historical_vol == 0.0);
    REQUIRE(result.max_drawdown == 0.0);
}

TEST_CASE("volatility throws on insufficient data", "[volatility]") {
    std::vector<double> one = {100.0};
    REQUIRE_THROWS_AS(munnir::compute_volatility(one), std::invalid_argument);
}

TEST_CASE("max drawdown is correct for known series", "[volatility]") {
    // 100 -> 80 is a 20% drawdown, then recovery
    std::vector<double> prices = {100.0, 90.0, 80.0, 95.0, 105.0};
    auto result = munnir::compute_volatility(prices);
    REQUIRE_THAT(result.max_drawdown, WithinRel(0.20, 1e-9));
}
```

Register the test in CMake:

```cmake
add_executable(tests
    tests/test_risk.cpp
    tests/test_portfolio.cpp
    tests/test_volatility.cpp   # new
)
target_link_libraries(tests PRIVATE munnir_engine_core Catch2::Catch2WithMain)
include(CTest)
include(Catch)
catch_discover_tests(tests)
```

Run with: `cd cpp_engine/build && cmake .. && cmake --build . && ctest --output-on-failure`

### 5. Expose to Python via pybind11

Add the binding in `cpp_engine/src/bindings.cpp`. This is the only file that touches pybind11:

```cpp
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>           // std::vector <-> Python list
#include <pybind11/numpy.h>         // py::array_t for zero-copy

#include "munnir_engine/volatility.hpp"

namespace py = pybind11;

// Zero-copy wrapper: accepts a NumPy array, passes a span to C++
py::dict compute_volatility_py(py::array_t<double> prices) {
    auto buf = prices.request();
    auto result = munnir::compute_volatility(
        std::span<const double>(static_cast<const double*>(buf.ptr), buf.size)
    );
    return py::dict(
        "historical_vol"_a = result.historical_vol,
        "annualized_vol"_a = result.annualized_vol,
        "max_drawdown"_a   = result.max_drawdown
    );
}

PYBIND11_MODULE(munnir_engine, m) {
    m.doc() = "Munnir high-performance compute engine";

    m.def("compute_volatility", &compute_volatility_py,
          py::arg("prices"),
          "Compute volatility metrics from a price series (NumPy array).");
}
```

After rebuilding, Python usage:

```python
import numpy as np
import munnir_engine

prices = np.array([100.5, 101.2, 99.8, 102.0, 98.5])
result = munnir_engine.compute_volatility(prices)
# {'historical_vol': 0.017..., 'annualized_vol': 0.27..., 'max_drawdown': 0.034...}
```

---

## Zero-Copy Data Transfer

When passing large arrays between Python and C++, always use `py::array_t<double>` instead of `std::vector<double>`:

```cpp
// GOOD — zero copy, reads NumPy memory directly
void process(py::array_t<double> data) {
    auto buf = data.request();
    auto* ptr = static_cast<const double*>(buf.ptr);
    size_t n = buf.size;
    // ptr points directly to NumPy's buffer — no copy
}

// BAD — pybind11 copies every element from the Python list into a new vector
void process(std::vector<double> data) {
    // data is a full copy of the Python list
}
```

For arrays with more than ~1000 elements, the difference is significant. For small arrays (< 100 elements), either is fine.

---

## Memory Safety Rules

- **No raw `new`/`delete`**. Use `std::unique_ptr` for single ownership, `std::shared_ptr` only when ownership is genuinely shared.
- **No raw C arrays**. Use `std::vector`, `std::array`, or `std::span`.
- **No manual index math on pointers**. Use range-based `for` loops or `std::span` with bounds.
- **RAII everywhere**. Resources (file handles, locks, allocations) are acquired in constructors and released in destructors. No cleanup functions.

If a segfault occurs, the most common causes are:

1. Accessing a `py::array_t` buffer after the Python object was garbage collected — always keep a reference alive.
2. Integer overflow in index calculations — use `size_t` for sizes and indices.
3. Passing an empty container to a function that assumes non-empty — validate inputs at the top of every public function.

---

## Build Troubleshooting

**"pybind11 not found"**: Make sure `pybind11` is installed in the active Python env. CMake finds it via `find_package(pybind11 REQUIRED)` which calls `pybind11-config`.

```bash
uv pip install pybind11
```

**"undefined symbol" at Python import time**: The `.so` was compiled but the symbol wasn't linked. Check that the new `.cpp` file is listed in `add_library(munnir_engine_core ...)` in CMakeLists.txt.

**"incompatible Python version"**: The `.so` was built against a different Python. Rebuild from scratch:

```bash
cd cpp_engine/build
rm -rf *
cmake .. -DPYTHON_EXECUTABLE=$(which python)
cmake --build .
```

**Catch2 FetchContent is slow**: It re-downloads on every clean build. Pin a specific release tag:

```cmake
FetchContent_Declare(
    Catch2
    GIT_REPOSITORY https://github.com/catchorg/Catch2.git
    GIT_TAG        v3.5.2
)
FetchContent_MakeAvailable(Catch2)
```

---

## Performance Guidelines

- Compile with `-O2` or `-O3` for production builds. Debug builds (`-O0 -g`) are 5–20x slower — never benchmark debug builds.
- Use `std::span` over `const std::vector<double>&` in function signatures — it's cheaper and accepts more input types.
- Avoid `std::map` in hot paths. Use `std::unordered_map` or sorted `std::vector` + binary search.
- For Monte Carlo simulations, use `std::mt19937_64` seeded from `std::random_device`. Never use `rand()`.
- Release the GIL for long computations so Python threads aren't blocked:

```cpp
py::dict long_simulation_py(py::array_t<double> params) {
    auto buf = params.request();
    py::gil_scoped_release release;  // release GIL during C++ work
    auto result = munnir::run_simulation(
        std::span<const double>(static_cast<const double*>(buf.ptr), buf.size)
    );
    py::gil_scoped_acquire acquire;  // re-acquire before touching Python objects
    return py::dict("result"_a = result);
}
```

---

## Common Pitfalls

- **Forgetting to add source files to CMakeLists.txt**: The code compiles but the symbol is missing at link time. Every new `.cpp` must be added to the `add_library` call.
- **Mixing up `std::span` lifetimes**: `std::span` doesn't own its data. If the underlying buffer goes out of scope, the span dangles. Never return a `std::span` from a function that creates the buffer locally.
- **Float comparison in tests**: Never use `==` for floating point. Use Catch2's `WithinRel` or `WithinAbs` matchers.
- **GIL deadlock**: If C++ calls back into Python (e.g., a callback) while the GIL is released, you deadlock. Either hold the GIL during callbacks or redesign to avoid them.
- **Header-only bloat**: Don't put implementations in headers. One change recompiles everything that includes it. Keep headers as declarations only.