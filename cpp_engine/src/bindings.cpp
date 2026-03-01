#include <pybind11/pybind11.h>
#include "munnir_engine/hello.hpp"
#include "munnir_engine/risk.hpp"
#include "munnir_engine/pnl.hpp"
#include "munnir_engine/position.hpp"

namespace py = pybind11;

PYBIND11_MODULE(munnir_engine, m) {
    m.doc() = "Munnir C++ math engine";

    // ── Hello (pipeline health check) ───────────────────────────────
    m.def("add", &munnir::add, "Add two integers",
          py::arg("a"), py::arg("b"));

    // ── Risk ────────────────────────────────────────────────────────
    py::enum_<munnir::RiskTolerance>(m, "RiskTolerance")
        .value("Low", munnir::RiskTolerance::Low)
        .value("Medium", munnir::RiskTolerance::Medium)
        .value("High", munnir::RiskTolerance::High);

    m.def("risk_percentage", &munnir::risk_percentage,
          "Base risk percentage for a tolerance level",
          py::arg("tolerance"));

    m.def("adjust_risk", &munnir::adjust_risk,
          "Dynamically adjust risk based on balance changes",
          py::arg("current_balance_cents"),
          py::arg("original_balance_cents"),
          py::arg("tolerance"));

    // ── P&L ─────────────────────────────────────────────────────────
    m.def("calculate_pnl", &munnir::calculate_pnl,
          "Absolute P&L in cents",
          py::arg("entry_price_cents"),
          py::arg("current_price_cents"),
          py::arg("quantity"));

    m.def("calculate_pnl_percentage", &munnir::calculate_pnl_percentage,
          "P&L as a ratio (e.g. 0.25 = 25% gain)",
          py::arg("entry_price_cents"),
          py::arg("current_price_cents"));

    // ── Position Sizing ─────────────────────────────────────────────
    // Enum overload: uses RiskTolerance to determine risk %.
    m.def("calculate_position",
          py::overload_cast<int64_t, munnir::RiskTolerance, double, int64_t>(
              &munnir::calculate_position),
          "Number of shares to buy (enum risk tolerance)",
          py::arg("balance_cents"),
          py::arg("tolerance"),
          py::arg("conviction"),
          py::arg("asset_price_cents"));

    // Double overload: explicit risk percentage.
    m.def("calculate_position_with_risk",
          py::overload_cast<int64_t, double, double, int64_t>(
              &munnir::calculate_position),
          "Number of shares to buy (explicit risk %)",
          py::arg("balance_cents"),
          py::arg("risk_pct"),
          py::arg("conviction"),
          py::arg("asset_price_cents"));
}
