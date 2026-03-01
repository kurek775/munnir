"""Interface to the C++ munnir_engine.

Falls back to a pure-Python implementation when the compiled module is not
available (e.g. during early development or CI without a C++ build).
"""

import logging

logger = logging.getLogger(__name__)

try:
    import munnir_engine as _engine  # type: ignore[import-untyped]

    def add(a: int, b: int) -> int:
        return _engine.add(a, b)

    logger.info("Using C++ munnir_engine")

except ImportError:
    logger.warning("C++ munnir_engine not found — using Python fallback")

    def add(a: int, b: int) -> int:
        return a + b
