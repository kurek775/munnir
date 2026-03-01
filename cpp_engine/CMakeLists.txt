cmake_minimum_required(VERSION 3.20)
project(munnir_engine VERSION 0.1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

# ── Core library (pure C++, no Python dependency) ──────────────────────
add_library(munnir_core STATIC
    src/math/hello.cpp
)
target_include_directories(munnir_core PUBLIC include)

# ── pybind11 Python module ─────────────────────────────────────────────
find_package(pybind11 CONFIG QUIET)
if(NOT pybind11_FOUND)
    include(FetchContent)
    FetchContent_Declare(
        pybind11
        GIT_REPOSITORY https://github.com/pybind/pybind11.git
        GIT_TAG        v2.13.6
    )
    FetchContent_MakeAvailable(pybind11)
endif()

pybind11_add_module(munnir_engine src/bindings.cpp)
target_link_libraries(munnir_engine PRIVATE munnir_core)

# ── Tests (Catch2) ─────────────────────────────────────────────────────
option(BUILD_TESTS "Build C++ tests" ON)
if(BUILD_TESTS)
    include(FetchContent)
    FetchContent_Declare(
        Catch2
        GIT_REPOSITORY https://github.com/catchorg/Catch2.git
        GIT_TAG        v3.7.1
    )
    FetchContent_MakeAvailable(Catch2)

    add_executable(munnir_tests tests/test_hello.cpp)
    target_link_libraries(munnir_tests PRIVATE munnir_core Catch2::Catch2WithMain)

    include(CTest)
    include(Catch)
    catch_discover_tests(munnir_tests)
endif()
