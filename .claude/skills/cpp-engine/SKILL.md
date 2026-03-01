---
name: cpp-engine
description: C++20 high-performance math engine with pybind11 bindings, CMake build, and Catch2 tests
---

# High-Performance Compute (The Math Engine)

While Python is great for orchestration, looping through thousands of simulated market ticks or calculating complex portfolio math is slow. C++ handles this heavy lifting.

* **Language:** Modern C++ (C++20 standard). We leverage modern standard library features for performance and safety.
* **Python Bindings:** `pybind11`. This library acts as a bridge, allowing us to compile C++ code into a binary file (`.so` on Linux, `.pyd` on Windows) that Python can import like a standard library.
* **Build Tools:** CMake. We use CMake to configure the build process, link necessary libraries, and manage the pybind11 integration.
* **Vectorized Math:** Using libraries like `Eigen` (if matrix math is needed later) or simply ensuring standard vectors (`std::vector`) are used efficiently.

## File Locations

| Purpose | Path |
|---------|------|
| CMake config | `cpp_engine/CMakeLists.txt` |
| Public headers | `cpp_engine/include/munnir_engine/` |
| Source / math modules | `cpp_engine/src/math/` |
| Market simulation | `cpp_engine/src/market/` |
| pybind11 wrapper | `cpp_engine/src/bindings.cpp` |
| Catch2 tests | `cpp_engine/tests/` |

## Testing

* **Framework:** Catch2 (v3, fetched via CMake FetchContent)
* **Run:** `cd cpp_engine/build && ctest --output-on-failure`
* **Convention:** One test file per source module, prefixed with `test_` (e.g., `test_hello.cpp`)

## Best Practices

* **Zero-Copy Data Transfer:** When passing large lists of stock prices from Python to C++, use `pybind11::array_t` (which interfaces with NumPy). This allows C++ to read the Python memory directly without creating a slow, duplicate copy of the data.
* **Memory Safety:** Strictly avoid raw pointers (`*`). Always use smart pointers like `std::unique_ptr` or `std::shared_ptr` (RAII principles) to guarantee that memory is freed and prevent memory leaks during long trading simulations.
* **Separation of Concerns:** Keep the core C++ trading math completely separate from the `pybind11` wrapper code. This makes the C++ logic easier to test in isolation using standard C++ testing frameworks (like Catch2 or Google Test).
