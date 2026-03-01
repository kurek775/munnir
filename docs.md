# Project Name: Project Munnir (Geopolitical Trading Simulator)

## 1. Project Overview & Brand Identity
**Munnir** (inspired by *Muninn*, one of Odin’s ravens in Norse mythology who flew across the world to gather news and secrets) is an advanced, risk-free paper-trading playground. 

The application simulates stock market investments based on real-time geopolitical news and market sentiment. Users can spin up multiple isolated "Trading Sessions," allocating virtual funds (e.g., $1000) and setting distinct risk profiles for the Munnir AI agent. The AI scours global events, formulates strategies, and executes virtual trades. The app features a highly interactive, drag-and-drop "dashboard playground" where users can compare different AI risk strategies side-by-side on interactive graphs. 

The stack is built for modern UI/UX and high-speed execution: Angular 21 (with Tailwind, Transloco, and CDK Drag&Drop), Python/FastAPI (for AI orchestration), and C++ (for high-speed market math and simulation).

## 2. Entities & Relationships

* **User**
    * **Attributes:** ID, Username, Email, PasswordHash, PreferredTheme (Light/Dark), PreferredLanguage (CS/EN)
    * **Relationships:** One-to-Many with 'TradingSessions'
* **TradingSession (The Playground Sandboxes)**
    * **Attributes:** ID, UserID, SessionName (e.g., "High Risk Euro War Scenario"), StartingBalance, CurrentBalance, RiskTolerance (Low, Medium, High), IsActive
    * **Relationships:** Belongs to 'User', One-to-Many with 'Holdings', One-to-Many with 'Trades'
* **Holding (Stock/Asset)**
    * **Attributes:** ID, SessionID, TickerSymbol, Quantity, AveragePurchasePrice, CurrentPrice
    * **Relationships:** Belongs to 'TradingSession'
* **Trade (Transaction Ledger)**
    * **Attributes:** ID, SessionID, TickerSymbol, Action (Buy/Sell), Quantity, ExecutionPrice, Justification (AI reasoning based on news), Timestamp
    * **Relationships:** Belongs to 'TradingSession'
* **MarketNews (Context)**
    * **Attributes:** ID, Headline, Source, SentimentScore, GeopoliticalRegion, ScrapedAt
    * **Relationships:** Many-to-Many with 'Trade'

## 3. System Inputs & Outputs

### Inputs
* **User Input:** Creating/Managing multiple Trading Sessions, drag-and-drop dashboard configuration, UI theme/language toggles.
* **External Data:** * Real-time stock market API data (e.g., Alpha Vantage, Yahoo Finance).
    * Geopolitical news feeds (via AI web scraping).
* **System Triggers:** Background Celery workers/cron jobs running the AI agent loop for active sessions.

### Outputs
* **Client Output:** Angular 21 rendered UI with real-time drag-and-drop dashboard, multi-session comparison charts (e.g., using Chart.js or ECharts), and trade history.
* **System Output:** DB records of simulated trades, C++ algorithmic backtesting results.
* **Logs & Analytics:** Agent decision logs, execution latency metrics.

---

## 4. Development Phases

### Phase 1: Project Initialization & Architecture
* **Goal:** Establish the foundation, repos, and folder structures.
* **Tasks:**
    * Initialize Angular 21 (FE) with Tailwind, Transloco, and Angular CDK (for drag-and-drop).
    * Initialize Python FastAPI (BE) and C++ core.
    * Establish the DB (PostgreSQL/SQLite).
* **Deliverable:** A live "Hello World" proving the Angular -> FastAPI -> C++ -> DB pipeline works.

### Phase 2: Core Playground & Auth
* **Goal:** Build the essential multi-session features.
* **Tasks:**
    * Implement User Auth.
    * Implement basic CRUD for "Trading Sessions" (users can create a $1000 low-risk session and a $5000 high-risk session).
    * Implement the Transloco language switcher (CS/EN) and Tailwind Dark/Light mode.
* **Deliverable:** A working app where a user can log in and create multiple blank trading sessions.

### Phase 3: The Munnir Agent & Math Engine (C++ / Python)
* **Goal:** Build the AI agent to fulfill the primary use case.
* **Tasks:**
    * Integrate LLM APIs to scrape/read geopolitical news.
    * Build the C++ evaluation engine to handle the math for position sizing, risk adjustment, and rapid execution simulation.
    * **Agent Communication Rule:** When the CLI tool/agent documents or explains the C++ trading math, algorithms, or any difficult math topics in the code comments or PRs, it must explain it assuming the reader is not smart. Start with simple analogies and concrete examples. Slowly add the formulas, explain each formula part by part, and then put it all together.
    * Create the execution loop that updates the session balances based on AI decisions.
* **Deliverable:** The core simulation loop is active; the AI trades independently across different sessions based on their assigned risk profiles.

### Phase 4: Drag-and-Drop Dashboard & Charting
* **Goal:** Make the playground "really cool" and highly interactive.
* **Tasks:**
    * Implement Angular CDK Drag and Drop to allow users to move active trading sessions around their dashboard as widgets.
    * Integrate a charting library to graph the performance of multiple sessions overlapping on the same chart (comparing High Risk vs Low Risk AI performance over time).
    * Build the UI to display the AI's "Justification" for every trade.
* **Deliverable:** A polished, highly interactive, graphical dashboard.

### Phase 5: Minimum Viable Product (MVP) Release
* **Goal:** Soft launch of the core product.
* **Tasks:**
    * Final manual QA testing.
    * Deploy MVP version to a staging server.
* **Deliverable:** V1.0 of Munnir is live and trading.

### Phase 6: Codebase Audit & Polish
* **Goal:** Resolve technical debt.
* **Tasks:**
    * Review C++ memory management, optimize DB queries, and ensure Angular components are lazy-loaded properly.
* **Deliverable:** A clean, optimized codebase ready for scaling.

---

## 5. Proposed Folder Structure

### 1. Front-End (Angular 21 Workspace)
```text
munnir-ui/
├── src/
│   ├── app/
│   │   ├── core/               # Singleton services, interceptors, auth guards
│   │   ├── shared/             # Reusable UI components (buttons, charts, drag-drop wrappers)
│   │   ├── features/           # Feature modules
│   │   │   ├── dashboard/      # Drag & Drop playground, main graphs
│   │   │   ├── sessions/       # Trading session CRUD, risk profile settings
│   │   │   └── trade-ledger/   # AI justification UI, transaction history
│   │   ├── assets/             # i18n JSON files (CS/EN), images, brand assets
│   │   ├── styles/             # Tailwind base layers, light/dark theme variables
│   │   └── app.routes.ts       # Standalone routing
│   ├── environments/
│   └── main.ts
├── tailwind.config.js
└── transloco.config.js

munnir-api/
├── app/
│   ├── api/
│   │   ├── v1/
│   │   │   ├── endpoints/      # FastAPI route definitions (users, sessions, trades)
│   │   ├── dependencies.py     # DB sessions, Auth extractors
│   ├── core/                   # Config, security, logging
│   ├── models/                 # SQLAlchemy ORM models
│   ├── schemas/                # Pydantic validation schemas
│   ├── services/               # Business logic
│   │   ├── ai_agent.py         # LLM integration, news scraping, sentiment analysis
│   │   └── simulation.py       # Interfaces with the C++ engine
│   └── db/                     # Migrations (Alembic)
├── cpp_engine/                 # -> (See C++ Core below)
├── requirements.txt
└── main.py


cpp_engine/
├── src/
│   ├── math/                   # Risk algorithms, position sizing logic
│   ├── market/                 # Simulated execution, slippage calculation
│   └── bindings.cpp            # Pybind11 Python wrappers
├── include/                    # Header files (.hpp)
├── tests/                      # Catch2 or GTest for C++ math validation
└── CMakeLists.txt              # Build configuration for creating the .so / .pyd file


