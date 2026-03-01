---
name: backend
description: Use this skill whenever building, modifying, or debugging the Munnir FastAPI backend — including API endpoints, SQLAlchemy models, Alembic migrations, Pydantic schemas, Celery background tasks, pydantic-settings configuration, or the pybind11 C++ engine integration. Trigger when the user mentions API routes, database models, migrations, request/response schemas, background jobs, or any Python backend work in the munnir-api directory. Also use when debugging 500 errors, fixing migration conflicts, adding new endpoints, or wiring up the C++ engine.
---

# Back-End Engineering — Munnir API

The FastAPI backend is the central orchestrator of Munnir. It handles HTTP routing, database transactions, background job dispatch, and coordinates the AI agent and C++ math engine.

## File Locations

| Purpose              | Path                                    |
| -------------------- | --------------------------------------- |
| App entry point      | `munnir-api/app/main.py`               |
| API v1 endpoints     | `munnir-api/app/api/v1/endpoints/`     |
| API v1 router        | `munnir-api/app/api/v1/router.py`      |
| Core config & DB     | `munnir-api/app/core/`                 |
| SQLAlchemy models    | `munnir-api/app/models/`              |
| Pydantic schemas     | `munnir-api/app/schemas/`             |
| Business logic       | `munnir-api/app/services/`            |
| Alembic migrations   | `munnir-api/alembic/`                 |
| Celery tasks         | `munnir-api/app/tasks/`               |
| Project config       | `munnir-api/pyproject.toml`           |

## Stack Summary

- **Runtime**: Python 3.12+, FastAPI (async)
- **Package manager**: uv
- **Database**: PostgreSQL (prod), SQLite (local dev), SQLAlchemy 2.0
- **Migrations**: Alembic
- **Validation**: Pydantic v2
- **Config**: pydantic-settings
- **Background jobs**: Celery + Redis broker
- **C++ interop**: `munnir_engine` via pybind11

---

## Adding a New Endpoint

Follow this sequence every time. Skipping steps causes runtime errors or schema mismatches.

### 1. Define the SQLAlchemy model

Create or update the model in `munnir-api/app/models/`. Use SQLAlchemy 2.0 mapped_column style:

```python
from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class Watchlist(Base):
    __tablename__ = "watchlists"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    ticker: Mapped[str] = mapped_column(String(10))

    user: Mapped["User"] = relationship(back_populates="watchlists")
```

Register the model import in `munnir-api/app/models/__init__.py` so Alembic discovers it.

### 2. Generate and review the migration

```bash
cd munnir-api
uv run alembic revision --autogenerate -m "add watchlists table"
```

**Always review the generated migration file.** Common issues autogenerate gets wrong:

- Drops tables or columns it doesn't recognize (especially if models aren't imported in `__init__.py`)
- Misses `index=True` on foreign keys
- Generates incorrect enum types or default values
- Doesn't handle data migrations (backfills) — you must write those manually

Apply with `uv run alembic upgrade head`. Roll back with `uv run alembic downgrade -1`.

### 3. Create Pydantic schemas

Define request and response schemas in `munnir-api/app/schemas/`. Keep them separate from SQLAlchemy models:

```python
from pydantic import BaseModel, Field

class WatchlistCreate(BaseModel):
    ticker: str = Field(..., pattern=r"^[A-Z]{1,5}$")

class WatchlistResponse(BaseModel):
    id: int
    ticker: str
    user_id: int

    model_config = {"from_attributes": True}
```

Use `from_attributes = True` (Pydantic v2) so you can pass SQLAlchemy model instances directly to the response schema.

### 4. Write the service layer

Put business logic in `munnir-api/app/services/`, not in the endpoint function. Endpoints should be thin — validate input, call service, return response:

```python
# app/services/watchlist.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.watchlist import Watchlist

async def add_to_watchlist(db: AsyncSession, user_id: int, ticker: str) -> Watchlist:
    item = Watchlist(user_id=user_id, ticker=ticker)
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item

async def get_user_watchlist(db: AsyncSession, user_id: int) -> list[Watchlist]:
    result = await db.execute(
        select(Watchlist).where(Watchlist.user_id == user_id)
    )
    return list(result.scalars().all())
```

### 5. Wire up the endpoint

Create the route in `munnir-api/app/api/v1/endpoints/` and register it in the v1 router:

```python
# app/api/v1/endpoints/watchlist.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.watchlist import WatchlistCreate, WatchlistResponse
from app.services.watchlist import add_to_watchlist, get_user_watchlist

router = APIRouter(prefix="/watchlists", tags=["watchlists"])

@router.post("/", response_model=WatchlistResponse, status_code=201)
async def create_watchlist_item(
    payload: WatchlistCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),  # auth dependency
):
    return await add_to_watchlist(db, current_user.id, payload.ticker)
```

Then add the router in `munnir-api/app/api/v1/router.py`:

```python
from app.api.v1.endpoints.watchlist import router as watchlist_router
api_router.include_router(watchlist_router)
```

---

## Database Session Management

Use FastAPI's `Depends()` to inject async sessions. Never create sessions manually in endpoint code:

```python
# app/core/database.py
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

engine = create_async_engine(settings.DATABASE_URL)
async_session = async_sessionmaker(engine, expire_on_commit=False)

async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session
```

For transactions that span multiple service calls, let the endpoint own the commit:

```python
async def complex_endpoint(db: AsyncSession = Depends(get_db)):
    await service_a(db)
    await service_b(db)
    await db.commit()  # single commit for both operations
```

---

## Configuration with pydantic-settings

All config lives in `munnir-api/app/core/config.py`:

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str = "redis://localhost:6379/0"
    OPENAI_API_KEY: str
    ANTHROPIC_API_KEY: str = ""
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

settings = Settings()
```

This validates that all required env vars exist at startup — the app won't boot with a missing `DATABASE_URL`. Add new env vars here, never read `os.environ` directly.

---

## Background Tasks with Celery

Long-running work (AI research loops, C++ computations, bulk scraping) goes through Celery. The frontend triggers the job via an API endpoint, and Celery runs it asynchronously.

### Task definition pattern

```python
# app/tasks/research.py
from app.core.celery_app import celery_app

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def run_research_cycle(self, user_id: int, portfolio_id: int):
    try:
        # Heavy AI + C++ work here
        ...
    except Exception as exc:
        self.retry(exc=exc)
```

### Triggering from an endpoint

```python
@router.post("/research/start")
async def start_research(current_user = Depends(get_current_user)):
    task = run_research_cycle.delay(current_user.id, current_user.portfolio_id)
    return {"task_id": task.id, "status": "started"}
```

### Task status polling

Provide a `/tasks/{task_id}/status` endpoint so the frontend can poll for completion. Return `PENDING`, `STARTED`, `SUCCESS`, or `FAILURE` from `AsyncResult(task_id).status`.

---

## C++ Engine Integration (pybind11)

The `munnir_engine` module is a compiled C++ library exposed to Python via pybind11. It handles numerically intensive operations (risk calculations, portfolio optimization, pricing models).

### Usage pattern

```python
import munnir_engine

# Pass Python types — pybind11 handles conversion
risk_score = munnir_engine.calculate_risk(
    prices=[100.5, 101.2, 99.8, 102.0],
    weights=[0.25, 0.25, 0.25, 0.25],
)
```

### Common issues

- **ImportError at runtime**: The compiled `.so`/`.pyd` file must match the Python version. Rebuild after Python upgrades with `uv run pip install -e munnir-engine/`.
- **Segfaults**: Usually caused by passing wrong types (e.g., a list of ints where floats are expected). Add type checking on the Python side before calling into C++.
- **Threading**: pybind11 holds the GIL by default. For CPU-heavy C++ calls, release it with `py::gil_scoped_release` in the C++ code, or run calls in Celery workers to avoid blocking the async event loop.
- **Never call `munnir_engine` directly inside an async endpoint** — it blocks the event loop. Always dispatch through Celery or `asyncio.to_thread()`.

---

## Testing

- **Framework**: pytest + pytest-asyncio + httpx
- **Run**: `cd munnir-api && uv run pytest`
- **Structure**: `munnir-api/tests/` mirrors `app/`

### Testing endpoints

```python
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac

@pytest.mark.asyncio
async def test_create_watchlist(client, auth_headers):
    resp = await client.post(
        "/api/v1/watchlists/",
        json={"ticker": "AAPL"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    assert resp.json()["ticker"] == "AAPL"
```

### Testing services

Test services directly with a test database session — don't go through HTTP unless you're testing the endpoint layer specifically.

---

## Common Pitfalls

- **Circular imports**: Models importing schemas importing models. Keep models, schemas, and services in separate layers. Use `TYPE_CHECKING` imports if you need type hints across layers.
- **Missing `await`**: Forgetting `await` on an async DB call returns a coroutine object instead of data. SQLAlchemy 2.0 async calls are all awaitable — if you get a coroutine where you expected a row, you missed an `await`.
- **Alembic head conflicts**: When multiple branches add migrations, you get a "multiple heads" error. Fix with `uv run alembic merge heads -m "merge"`.
- **N+1 queries**: Loading related objects in a loop. Use `selectinload()` or `joinedload()` in your SQLAlchemy queries to eager-load relationships.
- **Blocking the event loop**: Any synchronous call (C++ engine, file I/O, synchronous HTTP) inside an `async def` endpoint blocks all other requests. Use `asyncio.to_thread()` for sync work or dispatch to Celery.