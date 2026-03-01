---
name: ai-data
description: AI agent integration — LLM APIs, web scraping, prompt engineering, and structured output enforcement
user-invocable: false
---

# AI & Data Engineering (The Brain)

The Munnir agent relies on interpreting unstructured web data (news) and converting it into structured financial actions.

* **LLM Integration:** Integrating with OpenAI or Anthropic APIs.
* **Web Scraping:** Using `BeautifulSoup` or `Playwright` to extract geopolitical news headlines, article text, and metadata from target financial sites.
* **Prompt Engineering:** Designing system prompts that feed the AI the user's risk profile, the current portfolio state, and the scraped news, forcing a logical decision.
* **Structured Outputs:** Utilizing function calling or JSON mode to guarantee the AI responds with parsable data (e.g., `{"action": "BUY", "ticker": "AAPL", "confidence": 85, "reason": "..."}`).

## File Locations

| Purpose | Path |
|---------|------|
| AI agent service | `munnir-api/app/services/ai_agent.py` |
| News scraping | `munnir-api/app/services/scraper.py` |
| LLM prompt templates | `munnir-api/app/services/prompts/` |
| News model | `munnir-api/app/models/market_news.py` |

## Best Practices

* **Enforce JSON Schemas:** Never rely on the AI to "just format it correctly." Provide a strict Pydantic JSON schema to the LLM API to guarantee the structure of the response.
* **Handle Rate Limits & Retries:** AI APIs fail or rate-limit often. Implement exponential backoff (e.g., using the `Tenacity` library in Python) to automatically retry failed requests.
* **Audit Logging:** Save the *exact* raw prompt sent to the LLM and the *exact* raw response in the database alongside the executed trade. This is vital for debugging why the AI made a weird decision.
