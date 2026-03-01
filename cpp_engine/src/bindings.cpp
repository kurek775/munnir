#include <pybind11/pybind11.h>
#include "munnir_engine/hello.hpp"

namespace py = pybind11;

PYBIND11_MODULE(munnir_engine, m) {
    m.doc() = "Munnir C++ math engine";
    m.def("add", &munnir::add, "Add two integers",
          py::arg("a"), py::arg("b"));
}
