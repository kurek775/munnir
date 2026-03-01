FROM python:3.12-slim

# Build tools for C++ engine
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential cmake git && \
    rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

WORKDIR /app

# Install Python deps (no editable install — code is copied later)
COPY munnir-api/pyproject.toml .
RUN uv venv && \
    uv pip install \
        "fastapi>=0.115" \
        "uvicorn[standard]>=0.34" \
        "sqlalchemy[asyncio]>=2.0" \
        "aiosqlite>=0.20" \
        "alembic>=1.14" \
        "pydantic-settings>=2.7" \
        "pybind11>=2.13" \
        "pytest>=8.0" \
        "pytest-asyncio>=0.24" \
        "httpx>=0.28"

# Build C++ engine
COPY cpp_engine/ cpp_engine/
RUN cd cpp_engine && \
    mkdir -p build && cd build && \
    cmake .. -DBUILD_TESTS=ON \
        -Dpybind11_DIR="$(/app/.venv/bin/python -c 'import pybind11; print(pybind11.get_cmake_dir())')" \
        -DPYTHON_EXECUTABLE=/app/.venv/bin/python && \
    cmake --build . --parallel && \
    ctest --output-on-failure && \
    cp munnir_engine*.so /app/.venv/lib/python3.12/site-packages/ 2>/dev/null; \
    cp munnir_engine*.so /app/ 2>/dev/null; true

# Copy application code
COPY munnir-api/app app/
COPY munnir-api/alembic alembic/
COPY munnir-api/alembic.ini .
COPY munnir-api/tests tests/

# Create data dir for SQLite
RUN mkdir -p /app/data

EXPOSE 8000

CMD ["/app/.venv/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
