---
name: ai-data
description: Use this skill whenever building, modifying, or debugging the Munnir AI agent pipeline — including LLM API calls (OpenAI/Anthropic), web scraping of financial news, prompt template design, or structured output enforcement. Trigger this skill when the user mentions the AI agent, news scraping, trade signal generation, prompt engineering for Munnir, or anything involving converting unstructured news into structured financial actions. Also use when debugging why the agent made a bad trade recommendation, or when adding new data sources.
user-invocable: false
---

# AI & Data Engineering — Munnir Agent Pipeline

This skill covers the full pipeline that powers Munnir's AI-driven trade decisions: scraping financial news → feeding it to an LLM with context → extracting structured trade signals.

## File Locations

| Purpose                | Path                                        |
| ---------------------- | ------------------------------------------- |
| AI agent service       | `munnir-api/app/services/ai_agent.py`       |
| News scraping          | `munnir-api/app/services/scraper.py`        |
| LLM prompt templates   | `munnir-api/app/services/prompts/`          |
| News model             | `munnir-api/app/models/market_news.py`      |

## Architecture Overview

The pipeline flows in three stages:

1. **Scrape** — Pull headlines, article text, and metadata from target financial news sources.
2. **Contextualize** — Build a prompt combining scraped news + user risk profile + current portfolio state.
3. **Decide** — Send the prompt to an LLM and parse a structured trade signal from the response.

Each stage has its own failure modes. Design for them explicitly.

---

## Stage 1: Web Scraping

Use `BeautifulSoup` for static HTML sites and `Playwright` for JS-rendered pages.

### Key patterns

- Always set a realistic `User-Agent` header and respect `robots.txt`.
- Extract structured metadata (publish date, source, author) alongside article text — the LLM uses recency to weight decisions.
- Normalize all timestamps to UTC before storing.
- Implement a deduplication check (e.g., hash of headline + source) to avoid feeding the LLM duplicate articles.

### Error handling

- Wrap each scrape target in its own try/except so one broken site doesn't kill the whole pipeline.
- Log failed scrapes with the URL and error, and continue processing remaining sources.
- Set aggressive timeouts (10s for static, 30s for Playwright) — stale data is better than a hung pipeline.

---

## Stage 2: Prompt Engineering

Prompt templates live in `munnir-api/app/services/prompts/`. Each template is a Jinja2 file or Python string template.

### Prompt structure

Every prompt to the LLM should include these sections in order:

1. **System instruction** — Role definition, output format rules, and constraints (e.g., "You are a financial analyst. Respond ONLY with valid JSON matching the schema below.").
2. **User risk profile** — Injected from the user's settings (risk tolerance, sector preferences, max position size).
3. **Current portfolio state** — Ticker, quantity, average cost, current P&L for each holding.
4. **News context** — The scraped articles, ordered by recency, trimmed to fit the context window.
5. **Decision request** — The specific question: "Given this news and portfolio, what single trade action do you recommend?"

### Prompt hygiene

- Always include the JSON schema *inside* the system prompt, not just as a tool definition. Belt and suspenders.
- Cap the news context to ~60% of the available context window, leaving room for the system prompt, portfolio state, and response.
- Include a "think step by step" instruction before the final decision to improve reasoning quality.
- Never include raw HTML in the prompt — always clean article text to plain text before injection.

---

## Stage 3: Structured Output Enforcement

The LLM must return parsable, validated JSON. Never trust free-form text for trade decisions.

### Required output schema

Define a Pydantic model and use it for both API-level enforcement and application-level validation:

```python
from pydantic import BaseModel, Field
from typing import Literal

class TradeSignal(BaseModel):
    action: Literal["BUY", "SELL", "HOLD"]
    ticker: str = Field(..., pattern=r"^[A-Z]{1,5}$")
    confidence: int = Field(..., ge=0, le=100)
    reason: str = Field(..., min_length=10, max_length=500)
    risk_score: int = Field(..., ge=1, le=10)
```

### Enforcement strategy

- **OpenAI**: Use `response_format={"type": "json_schema", "json_schema": ...}` with the Pydantic model exported via `.model_json_schema()`.
- **Anthropic**: Use tool use / function calling with the schema as the tool's `input_schema`. Extract the result from the tool call block.
- **Fallback**: If the API doesn't enforce the schema, parse the response with `TradeSignal.model_validate_json(response_text)` and catch `ValidationError` explicitly.

### When parsing fails

- Log the raw response and the validation error.
- Retry once with a more explicit prompt ("Your previous response was not valid JSON. Respond ONLY with JSON matching this schema: ...").
- If the retry also fails, default to `HOLD` and alert the user — never execute a trade on unparseable output.

---

## Resilience & Retry Logic

AI APIs are unreliable. Use `tenacity` for retries:

```python
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import httpx

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.HTTPStatusError)),
)
async def call_llm(prompt: str) -> TradeSignal:
    ...
```

- Retry on 429 (rate limit), 500, 502, 503, and timeouts.
- Do NOT retry on 400 (bad request) — that's a prompt/schema bug, not a transient failure.
- Set a per-request timeout of 60s for LLM calls.

---

## Audit Logging

Every LLM call must be logged with:

- The exact prompt sent (full text, not a template reference)
- The exact raw response received
- The parsed `TradeSignal` (or the validation error if parsing failed)
- Timestamp, model name, and token usage
- The trade action taken (or "no action" if HOLD)

Store audit logs in the database alongside the trade record. This is essential for debugging why the agent made a bad call — you need to see exactly what it saw and what it said.

---

## Common Pitfalls

- **Context window overflow**: If you stuff too many articles in, the model truncates or degrades. Always measure token count before sending.
- **Stale news**: A 3-day-old headline can trigger a bad trade if the market already priced it in. Weight recency heavily or drop articles older than 24h.
- **Model drift**: LLM behavior changes across versions. Pin your model version (e.g., `gpt-4o-2024-08-06`, `claude-sonnet-4-20250514`) — don't use aliases like `gpt-4o` in production.
- **Confidence calibration**: The model's `confidence` score is not calibrated. Don't treat 85 as "85% likely to profit." Use it as a relative ranking signal, not an absolute probability.