---
name: domain
description: Algorithmic trading domain knowledge — portfolio math, position sizing, slippage, and the "explain like I'm not smart" documentation rule
user-invocable: false
---

# Domain Knowledge (Algorithmic Trading)

The math and logic must mimic the real world for the playground to be educational and realistic.

* **Portfolio Math:** Calculating Weighted Average Purchase Price, Realized vs. Unrealized PnL (Profit and Loss), and total portfolio value.
* **Position Sizing:** Calculating exactly how many shares to buy based on the portfolio's cash balance, the asset's price, and the session's risk profile.
* **Slippage & Fees:** Simulating realistic market conditions so the AI doesn't have a perfect, frictionless trading environment.

## File Locations

| Purpose | Path |
|---------|------|
| C++ math algorithms | `cpp_engine/src/math/` |
| C++ market simulation | `cpp_engine/src/market/` |
| Python simulation service | `munnir-api/app/services/simulation.py` |
| SQLAlchemy trade models | `munnir-api/app/models/` |

## Best Practices

* **Avoid Floating-Point Errors:** Never use standard floating-point numbers (`float` or `double`) to represent currency in the database or backend logic, as they can cause precision errors (e.g., $10.01 + $10.02 = $20.029999). Store all currency as integers representing cents (e.g., $10.00 is stored as `1000`), or use the `Decimal` type in Python/DB.
* **Explain Like I'm Not Smart (Documentation Rule):** The math must be accessible. If we implement a Position Sizing algorithm in C++, the documentation must break it down simply.

    *Example of the Documentation Rule in practice:*
    **Concept:** We need to figure out how many shares to buy.
    **Analogy:** Imagine you have $1000 in your wallet (Capital). You want to risk a maximum of 5% of your money ($50) on apples. If an apple costs $10 (Price), how many apples can you buy without risking more than $50? You can buy 5 apples.

    **Formulas:**
    First, we find the maximum amount of cash we are willing to risk:
    $RiskAmount = Capital \times RiskPercentage$

    Next, we figure out how many shares we can buy with that risk amount:
    $Shares = \frac{RiskAmount}{AssetPrice}$

    **Put it together:**
    If our AI has a $1000 portfolio and a 5% risk tolerance for a stock priced at $10:
    $RiskAmount = 1000 \times 0.05 = 50$
    $Shares = \frac{50}{10} = 5$ shares.
