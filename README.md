<p align="center">
  <img src="munnir-ui/src/assets/logo.svg" alt="Munnir" width="280" />
</p>

<h3 align="center">Geopolitical Trading Simulator</h3>

<p align="center">
  AI-driven trade signals from real-world news. C++ speed. Zero real money at risk.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Angular-21-dd0031?logo=angular" alt="Angular 21" />
  <img src="https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi" alt="FastAPI" />
  <img src="https://img.shields.io/badge/C%2B%2B-20-00599C?logo=cplusplus" alt="C++20" />
  <img src="https://img.shields.io/badge/Gemini-AI-4285F4?logo=google" alt="Gemini AI" />
  <img src="https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker" alt="Docker" />
</p>

---

## What is Munnir?

**Munnir** (named after Muninn, Odin's raven of memory) is a geopolitical trading simulator that turns real-world news into actionable trade signals using AI — then lets you execute, track, and learn from those trades without risking a single dollar.

Create trading sessions with virtual capital, set your risk tolerance, and let the AI analyst scan headlines for opportunities. Execute trades manually or flip on Auto-Pilot and watch the AI trade for you.

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Angular 21    │────▶│    FastAPI       │────▶│   C++20 Engine  │
│   Tailwind v4   │     │    SQLAlchemy    │     │   pybind11      │
│   ECharts       │     │    Gemini AI     │     │   Position Calc │
│   CDK Drag&Drop │     │    APScheduler   │     │   Risk Mgmt     │
│   Transloco i18n│     │    yfinance      │     │   P&L Math      │
└─────────────────┘     └─────────────────┘     └─────────────────┘
     :4200                   :8000                  linked via
     (UI)                    (API)                  pybind11
```

| Layer | Tech | Role |
|-------|------|------|
| **Frontend** | Angular 21, Tailwind CSS v4, ECharts, CDK | Interactive trading dashboard with drag-and-drop panels, balance charts, signal management |
| **Backend** | FastAPI, SQLAlchemy 2.0 async, Alembic | REST API, JWT auth, news ingestion, AI orchestration, trade execution |
| **AI Analyst** | Google Gemini 2.0 Flash | Reads news articles, generates BUY/SELL/HOLD signals with conviction scores and reasoning |
| **Math Engine** | C++20, pybind11, Catch2 | Position sizing, risk calculations, P&L math — all in cents to avoid floating-point errors |
| **Data** | SQLite + aiosqlite | Zero-config persistence with Alembic migrations |
| **News** | NewsAPI + RSS feeds | Real-time geopolitical news ingestion |
| **Prices** | yfinance | Live market prices for trade execution |

## Features

- **AI Trade Signals** — Gemini analyzes geopolitical news and generates signals with conviction percentages, risk scores, and detailed reasoning
- **Manual & Auto-Pilot** — Execute trades yourself or enable Auto-Pilot with configurable intervals (5 min to 24 hours)
- **Position Tracking** — Open/close positions with weighted average purchase price (WAPP) tracking and realized P&L
- **Balance Charts** — ECharts visualization of portfolio performance over time with trade markers
- **Slippage Simulation** — Realistic execution with slippage based on your risk tolerance level
- **Drag-and-Drop Dashboard** — Reorder session cards and detail panels to your preference
- **Trade Justification** — Every trade links back to the AI reasoning that triggered it ("Why?" expansion)
- **Dark/Light Theme** — Full theme system with amber accent, toggled via the navbar
- **Bilingual** — English and Czech via Transloco i18n
- **C++ Performance** — Position sizing and risk math run in compiled C++20, exposed to Python via pybind11

## Quick Start

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) & Docker Compose
- A [NewsAPI key](https://newsapi.org/register) (free tier: 100 req/day)
- A [Gemini API key](https://aistudio.google.com/apikey) (free tier available)

### 1. Clone & configure

```bash
git clone https://github.com/your-username/munnir.git
cd munnir
cp .env.example .env
# Edit .env with your API keys
```

### 2. Start

```bash
docker compose up --build
```

### 3. Use

| Service | URL |
|---------|-----|
| **UI** | [http://localhost:4200](http://localhost:4200) |
| **API** | [http://localhost:8000/docs](http://localhost:8000/docs) |

Register an account, create a trading session, and click **Analyze News** to get your first AI signal.

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NEWSAPI_KEY` | NewsAPI.org API key | — |
| `GEMINI_API_KEY` | Google Gemini API key | — |
| `NEWS_SCHEDULER_ENABLED` | Enable background news ingestion | `false` |
| `AUTOPILOT_ENABLED` | Enable auto-pilot scheduler | `false` |
| `AUTOPILOT_INTERVAL_MINUTES` | Auto-pilot cycle interval | `15` |
| `TRADE_FEE_CENTS` | Fee per trade in cents | `100` |
| `SLIPPAGE_ENABLED` | Simulate execution slippage | `true` |

## Project Structure

```
munnir/
├── munnir-ui/              # Angular 21 frontend
│   └── src/app/
│       ├── core/           # Services, guards, interceptors, models
│       └── features/       # Landing, auth, dashboard, session detail
├── munnir-api/             # FastAPI backend
│   └── app/
│       ├── api/v1/         # REST endpoints
│       ├── models/         # SQLAlchemy models
│       ├── schemas/        # Pydantic request/response schemas
│       ├── services/       # Business logic (AI, execution, news, prices)
│       └── core/           # Config, database, security
├── cpp_engine/             # C++20 math engine
│   ├── include/            # Public headers
│   ├── src/                # Implementation + pybind11 bindings
│   └── tests/              # Catch2 unit tests
├── docker-compose.yml      # One-command startup
└── .env.example            # Environment template
```

## How It Works

```
News Sources ──▶ Ingest ──▶ Gemini AI ──▶ Trade Signal
                                              │
                              ┌────────────────┤
                              ▼                ▼
                          Execute           Skip
                              │
                    ┌─────────┤
                    ▼         ▼
                  BUY       SELL ──▶ P&L Calculation
                    │                    │
                    ▼                    ▼
              Open Position      Close Position
                    │                    │
                    └────────┬───────────┘
                             ▼
                      Balance Update ──▶ Chart
```

1. **News Ingestion** — NewsAPI + RSS feeds pull geopolitical headlines
2. **AI Analysis** — Gemini reads articles with session context (balance, risk, recent signals) and outputs a structured signal
3. **Signal Review** — You see the action, asset, conviction %, risk score, and full reasoning
4. **Execution** — The C++ engine calculates position size, yfinance fetches live prices, slippage is simulated
5. **Tracking** — Positions track WAPP and cost basis; trades record every detail including AI justification
6. **Visualization** — Balance chart updates, P&L flows through the dashboard stats

## Tech Stack Details

| Category | Technology | Version |
|----------|-----------|---------|
| Frontend Framework | Angular | 21.2 |
| CSS | Tailwind CSS | 4.0 |
| Charts | ECharts + ngx-echarts | 6.0 / 21.0 |
| i18n | Transloco | 8.2 |
| Backend Framework | FastAPI | 0.115+ |
| ORM | SQLAlchemy | 2.0 (async) |
| AI Model | Google Gemini | 2.0 Flash |
| C++ Standard | C++20 | — |
| Python Bindings | pybind11 | 2.13 |
| C++ Tests | Catch2 | 3.7 |
| Package Mgmt (UI) | pnpm | 10.11 |
| Package Mgmt (API) | uv | latest |
| Containerization | Docker Compose | — |

## Development

### Frontend (outside Docker)

```bash
cd munnir-ui
pnpm install
pnpm start
```

### Backend (outside Docker)

```bash
cd munnir-api
uv sync
uv run uvicorn app.main:app --reload
```

### C++ Engine

The engine builds automatically inside Docker. To build locally:

```bash
cd cpp_engine
cmake -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build
ctest --test-dir build
```

## License

This project is for educational and simulation purposes only. Not financial advice. Not affiliated with any exchange or broker.

---

<p align="center">
  <sub>Named after <b>Muninn</b> — the raven who flies over Midgard and brings back memories of all he sees.</sub>
</p>
