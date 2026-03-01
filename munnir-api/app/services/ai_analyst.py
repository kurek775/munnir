"""AI analyst service — builds prompts, calls Gemini, parses structured trade signals."""

import asyncio
import json
import logging
import re

from google import genai
from tenacity import retry, stop_after_attempt, wait_exponential
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.news_article import NewsArticle
from app.models.trade_signal import TradeSignal
from app.models.trading_session import TradingSession
from app.models.user import User
from app.schemas.trade_signal import AnalyzeResponse, TradeSignalLLM, TradeSignalResponse
from app.services.news import get_recent_articles
from app.services.sessions import get_user_session

logger = logging.getLogger(__name__)

SIGNAL_JSON_SCHEMA = """{
  "action": "BUY" | "SELL" | "HOLD",
  "asset": "TICKER (1-5 uppercase letters)",
  "conviction": 0.0 to 1.0,
  "reasoning": "10-500 character explanation",
  "risk_score": 1 to 10
}"""


def _build_prompt(
    session: TradingSession,
    articles: list[NewsArticle],
    recent_signals: list[TradeSignal] | None = None,
) -> str:
    """Build a 5-section analysis prompt."""
    balance_dollars = session.current_balance / 100
    starting_dollars = session.starting_balance / 100
    pnl = balance_dollars - starting_dollars

    # Cap news content
    max_chars = settings.GEMINI_MAX_NEWS_TOKENS * 4
    news_sections = []
    char_count = 0
    for a in articles:
        snippet = f"**{a.title}** ({a.source})\n{a.content[:500]}"
        if char_count + len(snippet) > max_chars:
            break
        news_sections.append(snippet)
        char_count += len(snippet)

    news_text = "\n\n".join(news_sections) if news_sections else "No recent news available."

    # Build recent signals context to avoid repetition
    history_text = ""
    if recent_signals:
        history_lines = []
        for sig in recent_signals[:5]:
            history_lines.append(
                f"- {sig.action} {sig.asset} (conviction={sig.conviction:.0%}, "
                f"risk={sig.risk_score}) — {sig.action_taken}"
            )
        history_text = f"""

## Section 6: Recent Signals (avoid repeating)
Your previous recommendations for this session:
{chr(10).join(history_lines)}

IMPORTANT: Do NOT repeat the same action+asset combination as a recent signal unless the news context has changed significantly. Diversify your recommendations across different assets and strategies."""

    return f"""## Section 1: System Instruction
You are a geopolitical trading analyst AI. Analyze the provided news in context of the user's portfolio and produce exactly ONE trade signal as JSON.

You MUST respond with ONLY valid JSON matching this schema:
{SIGNAL_JSON_SCHEMA}

Rules:
- If no clear trade opportunity exists, respond with action "HOLD" and asset "CASH"
- conviction reflects your confidence (0.0 = no confidence, 1.0 = certain)
- risk_score reflects the risk of the trade (1 = very low risk, 10 = very high risk)
- reasoning must explain WHY this trade makes sense given the news

## Section 2: Risk Profile
Risk tolerance: {session.risk_tolerance}
- low: prefer HOLD or low-conviction trades, max risk_score 4
- medium: balanced approach, max risk_score 7
- high: aggressive trades acceptable, full risk_score range

## Section 3: Portfolio State
Starting balance: ${starting_dollars:,.2f}
Current balance: ${balance_dollars:,.2f}
P&L: ${pnl:+,.2f}

## Section 4: News Context
{news_text}

## Section 5: Decision Request
Based on the news above and the portfolio context, produce your trade signal as JSON.{history_text}"""


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=2, max=30))
def _call_gemini_sync(prompt: str) -> tuple[str, dict]:
    """Synchronous Gemini call (runs in thread). Returns (raw_text, usage_dict)."""
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    response = client.models.generate_content(
        model=settings.GEMINI_MODEL,
        contents=prompt,
        config=genai.types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.3,
        ),
    )
    raw_text = response.text or ""
    usage = {}
    if response.usage_metadata:
        usage = {
            "prompt_tokens": response.usage_metadata.prompt_token_count,
            "completion_tokens": response.usage_metadata.candidates_token_count,
            "total_tokens": response.usage_metadata.total_token_count,
        }
    return raw_text, usage


async def _call_gemini(prompt: str) -> tuple[str, dict]:
    """Async wrapper for Gemini call."""
    return await asyncio.to_thread(_call_gemini_sync, prompt)


def _parse_signal(raw_response: str) -> TradeSignalLLM | None:
    """Parse LLM response into validated TradeSignalLLM."""
    # Try direct parse
    try:
        return TradeSignalLLM.model_validate_json(raw_response)
    except Exception:
        pass

    # Fallback: extract JSON from markdown code blocks
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw_response, re.DOTALL)
    if match:
        try:
            return TradeSignalLLM.model_validate_json(match.group(1))
        except Exception:
            pass

    # Fallback: find first JSON object
    match = re.search(r"\{[^{}]*\}", raw_response, re.DOTALL)
    if match:
        try:
            return TradeSignalLLM.model_validate_json(match.group(0))
        except Exception:
            pass

    return None


def _default_hold_signal() -> TradeSignalLLM:
    """Return a safe HOLD signal when LLM parsing fails."""
    return TradeSignalLLM(
        action="HOLD",
        asset="CASH",
        conviction=0.0,
        reasoning="AI analysis failed to produce a valid signal. Defaulting to HOLD for safety.",
        risk_score=1,
    )


async def analyze_session(
    session_id: int, user: User, db: AsyncSession
) -> AnalyzeResponse:
    """Run AI analysis for a trading session."""
    if not settings.GEMINI_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GEMINI_API_KEY not configured",
        )

    # Load session (with ownership check)
    session = await get_user_session(session_id, user, db)

    # Ingest fresh news before analyzing
    from app.services.news import ingest_news
    await ingest_news(db)

    # Get recent articles
    articles = await get_recent_articles(db, max_age_hours=settings.NEWS_MAX_AGE_HOURS)

    # Fetch recent signals to give Gemini context (avoid repeating same recommendation)
    recent_sigs_result = await db.execute(
        select(TradeSignal)
        .where(TradeSignal.session_id == session_id)
        .order_by(TradeSignal.created_at.desc())
        .limit(5)
    )
    recent_signals = list(recent_sigs_result.scalars().all())

    # Build prompt and call Gemini
    prompt = _build_prompt(session, articles, recent_signals)
    raw_response, usage = await _call_gemini(prompt)

    # Parse response
    signal_data = _parse_signal(raw_response)
    if signal_data is None:
        logger.warning("Failed to parse Gemini response, defaulting to HOLD")
        signal_data = _default_hold_signal()

    # Pick the first article as the primary reference (if any)
    article_id = articles[0].id if articles else None

    # Store signal with full audit trail
    trade_signal = TradeSignal(
        session_id=session.id,
        article_id=article_id,
        action=signal_data.action,
        asset=signal_data.asset,
        conviction=signal_data.conviction,
        reasoning=signal_data.reasoning,
        risk_score=signal_data.risk_score,
        raw_prompt=prompt,
        raw_response=raw_response,
        model_used=settings.GEMINI_MODEL,
        prompt_tokens=usage.get("prompt_tokens"),
        completion_tokens=usage.get("completion_tokens"),
        total_tokens=usage.get("total_tokens"),
    )
    db.add(trade_signal)
    await db.commit()
    await db.refresh(trade_signal)

    return AnalyzeResponse(
        signal=TradeSignalResponse.model_validate(trade_signal),
        articles_used=len(articles),
    )


async def analyze_session_internal(
    session_id: int, db: AsyncSession
) -> TradeSignal | None:
    """Run AI analysis without user ownership check (for auto-pilot scheduler)."""
    if not settings.GEMINI_API_KEY:
        logger.warning("analyze_session_internal: GEMINI_API_KEY not configured")
        return None

    result = await db.execute(
        select(TradingSession).where(TradingSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        logger.warning("analyze_session_internal: session %d not found", session_id)
        return None

    articles = await get_recent_articles(db, max_age_hours=settings.NEWS_MAX_AGE_HOURS)

    # Fetch recent signals to avoid repeating same recommendation
    recent_sigs_result = await db.execute(
        select(TradeSignal)
        .where(TradeSignal.session_id == session_id)
        .order_by(TradeSignal.created_at.desc())
        .limit(5)
    )
    recent_signals = list(recent_sigs_result.scalars().all())

    prompt = _build_prompt(session, articles, recent_signals)
    raw_response, usage = await _call_gemini(prompt)

    signal_data = _parse_signal(raw_response)
    if signal_data is None:
        logger.warning("Failed to parse Gemini response, defaulting to HOLD")
        signal_data = _default_hold_signal()

    article_id = articles[0].id if articles else None

    trade_signal = TradeSignal(
        session_id=session.id,
        article_id=article_id,
        action=signal_data.action,
        asset=signal_data.asset,
        conviction=signal_data.conviction,
        reasoning=signal_data.reasoning,
        risk_score=signal_data.risk_score,
        raw_prompt=prompt,
        raw_response=raw_response,
        model_used=settings.GEMINI_MODEL,
        prompt_tokens=usage.get("prompt_tokens"),
        completion_tokens=usage.get("completion_tokens"),
        total_tokens=usage.get("total_tokens"),
    )
    db.add(trade_signal)
    await db.commit()
    await db.refresh(trade_signal)
    return trade_signal


async def get_session_signals(
    session_id: int, user: User, db: AsyncSession
) -> list[TradeSignal]:
    """Get all trade signals for a session (with ownership check)."""
    await get_user_session(session_id, user, db)
    result = await db.execute(
        select(TradeSignal)
        .where(TradeSignal.session_id == session_id)
        .order_by(TradeSignal.created_at.desc())
    )
    return list(result.scalars().all())
