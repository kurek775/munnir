---
name: domain
description: Algorithmic trading domain knowledge — portfolio math, position sizing, slippage, and the "explain like I'm not smart" documentation rule
user-invocable: false
---

# Domain Knowledge (Algorithmic Trading)

This skill is **not invoked directly**. It is referenced by other skills (backend, C++ engine) whenever trading logic, financial math, or simulation behavior needs to be implemented or documented. The math and logic must mimic the real world for the playground to be educational and realistic.

## File Locations

| Purpose | Path |
|---|---|
| C++ math algorithms | `cpp_engine/src/math/` |
| C++ market simulation | `cpp_engine/src/market/` |
| Python simulation service | `munnir-api/app/services/simulation.py` |
| SQLAlchemy trade models | `munnir-api/app/models/` |
| Domain unit tests (C++) | `cpp_engine/tests/math/` |
| Domain unit tests (Python) | `munnir-api/tests/domain/` |

---

## Golden Rule: Currency as Integers

**Never** use `float` or `double` for money — not in the database, not in Python, not in C++. Floating-point arithmetic causes precision drift (e.g., `10.01 + 10.02 = 20.029999...`).

| Layer | Representation | Type |
|---|---|---|
| Database | Cents as integer | `BIGINT` |
| Python | Cents as integer *or* `Decimal` | `int` / `decimal.Decimal` |
| C++ engine | Cents as integer | `int64_t` |
| Frontend display | Format at render time only | `(value / 100).toFixed(2)` |

```python
# CORRECT
price_cents: int = 1050   # $10.50

# WRONG — never do this
price: float = 10.50
```

```cpp
// CORRECT
int64_t price_cents = 1050;  // $10.50

// WRONG
double price = 10.50;
```

All conversions to human-readable dollars happen **only** at the presentation layer (frontend or API response serialization). Internal math is always in cents.

---

## Core Formulas

Every formula below follows the **Explain Like I'm Not Smart** documentation rule (see section at the end). When implementing any of these, the code comments and docs must include the analogy, the formula, and a worked example.

### 1. Position Sizing

**Concept:** How many shares can the AI buy without exceeding its risk budget?

**Analogy:** You have $1,000 in your wallet. You're willing to risk 5% ($50) on apples. Each apple costs $10. You can buy 5 apples.

**Formulas:**

$$RiskAmount = Capital \times RiskPercentage$$

$$Shares = \lfloor \frac{RiskAmount}{AssetPrice} \rfloor$$

The floor (`⌊ ⌋`) is critical — you cannot buy fractional shares in Munnir.

**Worked example:**
- Capital = $1,000 (100,000 cents)
- Risk = 5%
- Asset price = $10.00 (1,000 cents)
- RiskAmount = 100,000 × 0.05 = 5,000 cents
- Shares = ⌊5,000 / 1,000⌋ = **5 shares**

```cpp
// cpp_engine/src/math/position_sizing.h
int64_t calculate_shares(int64_t capital_cents, double risk_pct, int64_t price_cents) {
    int64_t risk_amount = static_cast<int64_t>(capital_cents * risk_pct);
    if (price_cents <= 0) return 0;
    return risk_amount / price_cents;  // integer division = implicit floor
}
```

```python
# munnir-api/app/services/simulation.py
def calculate_shares(capital_cents: int, risk_pct: float, price_cents: int) -> int:
    if price_cents <= 0:
        return 0
    risk_amount = int(capital_cents * risk_pct)
    return risk_amount // price_cents
```

**Edge cases to handle:**
- `price_cents <= 0` → return 0 (cannot divide by zero)
- `risk_amount < price_cents` → return 0 (can't afford a single share)
- `capital_cents <= 0` → return 0 (no money to invest)

---

### 2. Weighted Average Purchase Price (WAPP)

**Concept:** When the AI buys the same stock multiple times at different prices, what is its true average cost per share?

**Analogy:** You buy 3 apples at $2 each and 2 apples at $3 each. You didn't pay "$2.50 per apple" — you paid $(3×2 + 2×3) / 5 = $2.40 per apple. The bigger purchase pulls the average toward its price.

**Formula:**

$$WAPP = \frac{\sum (Shares_i \times Price_i)}{\sum Shares_i}$$

**Worked example:**
- Buy 1: 10 shares × $50 = $500
- Buy 2: 5 shares × $60 = $300
- WAPP = (500 + 300) / (10 + 5) = 800 / 15 = **$53.33**

```cpp
// cpp_engine/src/math/portfolio_math.h
struct Purchase {
    int64_t shares;
    int64_t price_cents;
};

int64_t calculate_wapp(const std::vector<Purchase>& buys) {
    int64_t total_cost = 0;
    int64_t total_shares = 0;
    for (const auto& b : buys) {
        total_cost += b.shares * b.price_cents;
        total_shares += b.shares;
    }
    if (total_shares == 0) return 0;
    return total_cost / total_shares;
}
```

**Edge cases:**
- Zero total shares → return 0
- Single purchase → WAPP equals that purchase price exactly
- After a **full sell**, WAPP resets on the next buy

---

### 3. Profit & Loss (PnL)

**Concept:** How much money has the AI made or lost?

**Analogy:** You bought 10 apples at $2 each ($20 total). Today apples are worth $3 each. If you sold right now, you'd get $30 — that's $10 of *unrealized* profit (you haven't sold yet). If you sell 5 apples at $3, you pocket $15 on a $10 cost — that's $5 of *realized* profit.

#### Unrealized PnL (paper gains/losses — still holding)

$$UnrealizedPnL = (CurrentPrice - WAPP) \times HeldShares$$

#### Realized PnL (locked in — shares sold)

$$RealizedPnL = (SellPrice - WAPP_{at\ time\ of\ sale}) \times SoldShares$$

#### Total PnL

$$TotalPnL = RealizedPnL + UnrealizedPnL$$

**Worked example:**
- Bought 10 shares, WAPP = $50 (5,000 cents)
- Sold 4 shares at $60 (6,000 cents)
- Current price = $55 (5,500 cents)
- RealizedPnL = (6,000 − 5,000) × 4 = **4,000 cents ($40)**
- UnrealizedPnL = (5,500 − 5,000) × 6 = **3,000 cents ($30)**
- TotalPnL = 4,000 + 3,000 = **7,000 cents ($70)**

```python
def calculate_unrealized_pnl(current_price_cents: int, wapp_cents: int, held_shares: int) -> int:
    return (current_price_cents - wapp_cents) * held_shares

def calculate_realized_pnl(sell_price_cents: int, wapp_cents: int, sold_shares: int) -> int:
    return (sell_price_cents - wapp_cents) * sold_shares
```

---

### 4. Portfolio Value

**Concept:** What is the AI's portfolio worth right now?

**Formula:**

$$PortfolioValue = CashBalance + \sum (HeldShares_i \times CurrentPrice_i)$$

**Edge case:** A portfolio with zero positions is worth exactly its cash balance.

---

### 5. Slippage & Fees

**Concept:** In the real world, you never get the exact price you see on screen. Slippage simulates this friction so the AI learns to account for it.

**Analogy:** You see apples listed at $2.00, but by the time you reach the cashier, the price shifted to $2.03. That 3-cent difference is slippage. The cashier also charges a $0.05 transaction fee. Your true cost per apple is $2.08.

#### Slippage Model

```
ExecutionPrice = MarketPrice × (1 + SlippageFactor × Direction)
```

Where:
- `Direction` = +1 for buys (you pay more), −1 for sells (you receive less)
- `SlippageFactor` = a small random value drawn from a configurable range

| Risk Profile | Slippage Range | Description |
|---|---|---|
| Conservative | 0.001 – 0.003 (0.1%–0.3%) | Stable, liquid assets |
| Moderate | 0.003 – 0.008 (0.3%–0.8%) | Average market conditions |
| Aggressive | 0.008 – 0.020 (0.8%–2.0%) | Volatile / low-liquidity |

#### Fee Model

A flat per-trade fee in cents, applied after slippage:

$$TotalCost = (ExecutionPrice \times Shares) + FeeCents$$

```cpp
// cpp_engine/src/market/slippage.h
#include <random>

struct SlippageConfig {
    double min_factor;
    double max_factor;
    int64_t fee_cents;
};

int64_t apply_slippage(int64_t market_price_cents, int direction,
                       const SlippageConfig& config, std::mt19937& rng) {
    std::uniform_real_distribution<double> dist(config.min_factor, config.max_factor);
    double factor = dist(rng);
    double adjusted = market_price_cents * (1.0 + factor * direction);
    return static_cast<int64_t>(std::round(adjusted));
}
```

```python
import random

def apply_slippage(
    market_price_cents: int,
    direction: int,  # +1 buy, -1 sell
    min_factor: float,
    max_factor: float,
) -> int:
    factor = random.uniform(min_factor, max_factor)
    adjusted = market_price_cents * (1.0 + factor * direction)
    return round(adjusted)
```

**Edge cases:**
- Slippage is **always** unfavorable — buys cost more, sells receive less
- Slippage factor of 0.0 = frictionless (only used in tests, never in production sims)
- Fees are deducted from the cash balance *after* the trade executes

---

## The "Explain Like I'm Not Smart" Documentation Rule

Every formula, algorithm, or non-trivial piece of domain logic **must** be documented with all four of these parts:

1. **Concept** — One sentence: what problem does this solve?
2. **Analogy** — Explain it using everyday objects (apples, wallets, shopping). No jargon.
3. **Formula** — The mathematical notation.
4. **Worked Example** — Plug in real numbers and show every step.

This rule applies to:
- C++ header/source comments
- Python docstrings
- API documentation
- This skill file itself

If a new contributor can't understand the logic within 60 seconds of reading the docs, the documentation has failed.

### Template for Code Comments

```cpp
/**
 * Calculate Weighted Average Purchase Price (WAPP)
 *
 * CONCEPT: When buying the same asset at different prices, this gives
 *          the true average cost per share.
 *
 * ANALOGY: Buy 3 apples at $2 and 2 at $3. Average isn't $2.50 —
 *          it's (3×2 + 2×3) / 5 = $2.40. Bigger purchases pull the average.
 *
 * FORMULA: WAPP = Σ(shares_i × price_i) / Σ(shares_i)
 *
 * EXAMPLE: Buy1: 10 × $50 = $500, Buy2: 5 × $60 = $300
 *          WAPP = (500 + 300) / 15 = $53.33
 */
```

---

## Testing Domain Logic

Domain math is the foundation — if it's wrong, everything built on top is wrong. Test aggressively.

### What to Test

| Scenario | Why |
|---|---|
| Standard cases | Confirm the formula works |
| Zero inputs (0 shares, 0 capital, 0 price) | Guard against division by zero |
| Single purchase/sale | WAPP equals purchase price, PnL is straightforward |
| Multiple buys then partial sell | Verify WAPP doesn't change, realized PnL is correct |
| Full sell then new buy | WAPP must reset |
| Very large values | Ensure `int64_t` doesn't overflow at scale |
| Slippage bounds | Execution price always worse than market price |

### Test File Locations

| Layer | Path |
|---|---|
| C++ math tests | `cpp_engine/tests/math/` |
| C++ market tests | `cpp_engine/tests/market/` |
| Python domain tests | `munnir-api/tests/domain/` |

### Example Test

```python
# munnir-api/tests/domain/test_position_sizing.py
import pytest
from app.services.simulation import calculate_shares

class TestPositionSizing:
    def test_standard_case(self):
        # $1000 capital, 5% risk, $10 stock
        assert calculate_shares(100_000, 0.05, 1_000) == 5

    def test_zero_price_returns_zero(self):
        assert calculate_shares(100_000, 0.05, 0) == 0

    def test_insufficient_risk_budget(self):
        # $100 capital, 1% risk = $1 budget, stock costs $5
        assert calculate_shares(10_000, 0.01, 500) == 0

    def test_no_capital(self):
        assert calculate_shares(0, 0.05, 1_000) == 0

    def test_fractional_shares_floored(self):
        # $1000 capital, 5% risk = $50 budget, stock costs $12
        # 50 / 12 = 4.16 → floor to 4
        assert calculate_shares(100_000, 0.05, 1_200) == 4
```

---

## Checklist Before Implementing Domain Logic

1. All money stored and computed as **integer cents** (`int64_t` / `int`)
2. Formula documented with all 4 parts (Concept, Analogy, Formula, Worked Example)
3. Edge cases for zero, negative, and overflow handled explicitly
4. Slippage always unfavorable (buy price up, sell price down)
5. WAPP recalculated on every buy, reset on full liquidation
6. Realized PnL uses WAPP **at time of sale**, not current WAPP
7. Unit tests cover standard, zero, boundary, and large-value cases