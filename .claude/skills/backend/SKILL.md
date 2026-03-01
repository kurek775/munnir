---
name: backend
description: FastAPI backend with SQLAlchemy, Alembic migrations, pydantic-settings, and C++ engine integration via pybind11
---

# Back-End Engineering (The Orchestrator)

The Python backend is the central nervous system of Munnir. It handles API routing, database transactions, and coordinates the AI agents and C++ math engines.

* **Core Framework:** Python 3.12+ and FastAPI. FastAPI provides high-performance, asynchronous endpoints out of the box.
* **Package Manager:** uv. Fast Python package management and virtual environments.
* **Data Validation:** Pydantic. Used for defining strict schemas for API requests, database serialization, and enforcing structured JSON outputs from the LLM.
* **Database & ORM:** PostgreSQL for production (SQLite for local dev), managed via SQLAlchemy 2.0. We use Alembic for version-controlled database schema migrations.
* **Background Processing:** Celery (with Redis as a broker). The AI's research and trading loops take time. The frontend triggers the job, and Celery runs the heavy AI/C++ tasks in the background without blocking the main API.
* **Interoperability:** The backend uses `import munnir_engine` (created via pybind11) to pass Python objects (like risk scores or arrays of prices) into the C++ engine for processing.

## File Locations

| Purpose | Path |
|---------|------|
| App entry point | `munnir-api/app/main.py` |
| API v1 endpoints | `munnir-api/app/api/v1/endpoints/` |
| API v1 router | `munnir-api/app/api/v1/router.py` |
| Core config & DB | `munnir-api/app/core/` |
| SQLAlchemy models | `munnir-api/app/models/` |
| Pydantic schemas | `munnir-api/app/schemas/` |
| Business logic | `munnir-api/app/services/` |
| Alembic migrations | `munnir-api/alembic/` |
| Project config | `munnir-api/pyproject.toml` |

## Testing

* **Framework:** pytest (with `pytest-asyncio` for async tests, `httpx` for API testing)
* **Run:** `uv run pytest` inside the `munnir-api/` directory
* **Convention:** Place tests in `munnir-api/tests/` mirroring the `app/` structure

## Best Practices

* **Dependency Injection:** Use FastAPI's `Depends()` for database sessions and user authentication to keep route logic clean and easily testable.
* **Alembic Migrations:** Never blindly trust auto-generated migrations. Always manually review the Alembic output to ensure it's not dropping important tables or missing complex relationships.
* **Configuration Management:** Use `pydantic-settings` to manage environment variables (API keys, DB URLs). It validates that all necessary keys are present before the app even starts.
