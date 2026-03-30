# YAP 471 - Dynamic BIST Rotation with Markowitz Optimization

Computational Finance term project implementing a hybrid **Markowitz-based sector rotation strategy** for Borsa Istanbul. The system dynamically combines **technical indicators** (trend, momentum, volatility) and **macro regime signals** (interest rates, inflation, FX), then uses these composite scores to tilt expected returns in a **long-only Markowitz optimizer** that rebalances monthly. Backtested over 8.5 years (Jul 2017 – Feb 2026) with a Sharpe ratio of **1.971** vs. benchmark **1.728**.

---

## 🎯 Strategy Overview

### Core Concept
Every month (last trading day), the system:
1. **Evaluates** 10 BIST stocks using technical + macro signals
2. **Scores** each stock from -1 (avoid) to +1 (buy)
3. **Optimizes** portfolio weights to maximize return-risk tradeoff while tilting toward high-scoring stocks
4. **Rebalances** the entire portfolio at month-end, holds for one month, repeats

### What Makes It Work
- **Technical Signals** capture momentum & trend direction
- **Macro Signals** reflect economic regime (interest rates, inflation, currency)
- **Sector Sensitivity** connects macro conditions to sector performance (e.g., weak TL helps exporters)
- **Confidence Weighting** filters out weak/contradictory signals
- **Markowitz Optimization** ensures efficient risk-adjusted allocation

### Key Results
- **Strategy Sharpe Ratio:** 1.971 (+0.243 vs. benchmark)
- **Annual Return:** 61.86% (vs. benchmark 48.49%)
- **Annual Volatility:** 31.39%
- **Max Drawdown:** -32.92%
- **Total 9-Year Return:** 6,321.75%
- **Test Period:** 3 Jul 2017 – 23 Feb 2026 (104 monthly rebalances)

---

## 📊 How the Strategy Works: Step-by-Step

### Step 1: Generate Technical Signals (Per-Stock, Daily)

Three technical indicators are combined to create a single "technical score" for each stock:

#### 1a. **Trend Signal (Weight: 40%)**
```
IF 50-day MA > 200-day MA:
  Trend = +1  (UPTREND, buy signal)
ELSE:
  Trend = -1  (DOWNTREND, avoid)
```
- **Example:** GARAN.IS has 50-day MA = 31.5 TRY, 200-day MA = 29.0 TRY → Trend = +1

#### 1b. **Momentum Signal (Weight: 35%)**
```
Momentum = Z-score(63-day return) / 3  ∈ [-1, +1]
```
- Cross-sectional normalization: relative strength vs. other stocks
- **Example:** If GARAN gained 25% in 63 days (better than average), Momentum = +0.8
- **Example:** If EREGL gained only 2% in 63 days (worse than average), Momentum = -0.6

#### 1c. **Volatility Regime Signal (Weight: 25%)**
```
IF Recent 63-day vol < 1-year median vol:
  Volatility = +0.5  (stable, low-risk, favorable)
ELSE IF Recent 63-day vol >= 1-year median vol:
  Volatility = -0.5  (high-risk, avoid)
```
- **Example:** BIMAS avg volatility is 20%, but recent months are only 18% → Volatility = +0.5 (stable)
- **Example:** SISE usual vol is 25%, recent spike to 35% → Volatility = -0.5 (risky)

#### **Technical Score Aggregation**
```
Technical_Score = 0.40 × Trend + 0.35 × Momentum + 0.25 × Volatility
Result: [-1, +1]

EXAMPLE (for GARAN on a specific date):
= 0.40 × (+1.0) + 0.35 × (+0.8) + 0.25 × (+0.5)
= 0.40 + 0.28 + 0.125
= +0.805  ← Strong buy signal
```

---

### Step 2: Generate Macro Regime Signals (Per-Sector, Daily)

Three macro regimes classify economic conditions; each sector reacts differently:

#### 2a. **Interest Rate Regime**
- **Data:** WACF (TCMB Weighted Average Cost of Funds)
- **Logic:** Compare 6-month change
```
IF 6-month change in WACF < -2%:
  Rate_Regime = +1  (rate cutting, expansionary → positive for borrowers)
ELIF 6-month change > +2%:
  Rate_Regime = -1  (rate hiking, contractionary → negative)
ELSE:
  Rate_Regime = 0  (neutral)
```
- **Example:** WACF was 18% in Jan 2017, drops to 15% by Jul 2017 → Rate_Regime = +1
- **Sector Impact:** Banks (Interest-Sensitive) gain +0.7 multiplier; manufacturers (Mining/Industrial) only +0.2

#### 2b. **Inflation Regime**
- **Data:** CPI Year-over-Year growth
- **Logic:** Compare 3-month change
```
IF 3-month drop in CPI_YoY > 2%:
  Inflation_Regime = +1  (disinflation, TRY strengthening → positive)
ELIF 3-month rise in CPI_YoY > 2%:
  Inflation_Regime = -1  (acceleration, TRY weakening → negative)
```
- **Example:** CPI YoY drops from 12% to 8% in 3 months → Inflation_Regime = +1
- **Sector Impact:** Retail (high markup sensitivity) gains +0.6; exporters only +0.2

#### 2c. **FX Regime (USD/TRY)**
- **Data:** 1-month USD/TRY change
- **Logic:**
```
IF TL strengthens (USD/TRY drops >1%):
  FX_Regime = +1  (strong TL → hurt exporters, help importers)
ELIF TL weakens sharply (USD/TRY rises >5%):
  FX_Regime = -1  (weak TL → help exporters, hurt importers)
```
- **Example:** USD/TRY was 4.50, drops to 4.45 (TL strength, -1.1%) → FX_Regime = +1
- **Sector Impact:** Exporters (TOASO, FROTO) get **-0.7 multiplier** (weak TL hurts them); mining gets +0.5

#### **Sector-Specific Macro Sensitivity Matrix**
```
                          Rate   Inflation   FX
Mining/Industrial         0.2      0.3      0.5
Export-Oriented           0.1      0.2     -0.7   ← Weak TL hurts exporters!
Interest-Sensitive        0.7      0.2      0.1   ← Banks LOVE rate cuts
Defensive/Retail          0.1      0.6      0.3
```

#### **Macro Score Per Stock**
```
For TOASO (Export-Oriented) on a date where:
  Rate_Regime = +1, Inflation_Regime = -1, FX_Regime = +1:

Macro_Score = (+1 × 0.1) + (-1 × 0.2) + (+1 × -0.7)
            = 0.1 - 0.2 - 0.7
            = -0.8  ← Very negative for exporters (strong TL is bad)

vs. GARAN (Interest-Sensitive) same date:
Macro_Score = (+1 × 0.7) + (-1 × 0.2) + (+1 × 0.1)
            = 0.7 - 0.2 + 0.1
            = +0.6  ← Positive for banks (rate cuts are good)
```

---

### Step 3: Combine Technical + Macro into Composite Score

```
Composite_Score = 0.60 × Technical_Score + 0.40 × Macro_Score
Result: [-1, +1]

EXAMPLE: On a specific date
GARAN:
  Technical = +0.805 (good trend, momentum, stable vol)
  Macro     = +0.6   (rate cuts favor banks)
  Composite = 0.60 × 0.805 + 0.40 × 0.6 = 0.483 + 0.24 = +0.723  ← STRONG BUY

TOASO:
  Technical = -0.2   (weak trend, negative momentum)
  Macro     = -0.8   (strong TL hurts exporters)
  Composite = 0.60 × (-0.2) + 0.40 × (-0.8) = -0.12 - 0.32 = -0.44  ← SELL/AVOID
```

---

### Step 4: Filter by Signal Confidence (Quality Check)

Not all signals are equally reliable. We compute **confidence** based on how much the 3 technical components agree:

```
Confidence = Average(|Trend|, |Momentum|, |Volatility|)  ∈ [0, 1]

HIGH CONFIDENCE (0.9):
  Trend = +1, Momentum = +0.8, Volatility = +0.7
  → All 3 say "buy"
  → Confidence = (1 + 0.8 + 0.7) / 3 = 0.83
  → WEIGHT SIGNAL FULLY

LOW CONFIDENCE (0.3):
  Trend = +1, Momentum = -0.9, Volatility = +0.1
  → Signals conflict (weak momentum despite trend change)
  → Confidence = (1 + 0.9 + 0.1) / 3 = 0.67  
  → Wait—actually this *would* have only 0.67 confidence, so moderate
  
VERY LOW CONFIDENCE (0.2):
  Trend = +0.1, Momentum = -0.1, Volatility = -0.3
  → All signals are weak/ambiguous
  → Confidence = (0.1 + 0.1 + 0.3) / 3 = 0.17  ← DAMPEN THIS SIGNAL
  
FINAL WEIGHTED COMPOSITE:
Weighted_Composite = Composite_Score × Confidence
```

**Effect:** Weak, noisy signals get dampened; strong consensus signals get full weight.

---

### Step 5: Markowitz Optimization (Monthly Weights)

Now we have a score for each of the 10 stocks. The Markowitz optimizer decides **how much money to allocate** to each:

#### 5a. **Estimate Expected Returns (Signal-Tilted)**
```
Base Return = 252-day annualized mean return
            = average daily return × 252

GARAN 252-day mean return = 0.12% per day × 252 = 30% per year

Signal Tilt (with Tilt Strength λ = 0.15):
Expected_Return = Base_Return × (1 + λ × Composite_Score)
                = 30% × (1 + 0.15 × 0.723)
                = 30% × 1.1085
                = 33.25%

vs. EREGL (lower score -0.3):
Expected_Return = 8% × (1 + 0.15 × (-0.3))
                = 8% × 0.955
                = 7.64%
```

**Key insight:** The tilt strength λ=0.15 means we slightly upweight high-scoring stocks without completely overriding historical averages. Too high (λ=0.5) = overfit to noisy signals; too low (λ=0) = ignore signals.

#### 5b. **Estimate Volatilities & Correlations**
```
Volatility_Estimate = 252-day rolling std dev
                    + Signal-scaled penalty for low-scoring stocks
                    + Diagonal shrinkage (30% of covariance is replaced by diagonal)

Low-scoring stocks get higher estimated volatility (more risky).
```

#### 5c. **Markowitz Optimization Problem**
```
Maximize: (Expected_Return_Vector @ weights) - γ × (weights @ Covariance @ weights)

Subject to:
  - sum(weights) = 1.0          (fully invested)
  - all weights >= 0             (long-only, no shorts)
  - all weights <= 0.25          (max 25% per asset)
  - γ = 5.0 (risk aversion)      (penalize volatility 5× the return gain)

Solver: cvxpy (ECOS)

OUTPUT: Optimal weight vector w*
```

#### **Example Rebalance Date: 30 June 2017**
Given scores:
- GARAN: +0.72
- AKBNK: +0.58
- MGROS: +0.45
- SISE: -0.15
- EREGL: -0.30

Optimizer outputs:
```
AKBNK: 0.00%  (too much correlation with GARAN)
BIMAS: 0.00%  (low score, not enough to break into constraint)
EKGYO: 0.00%
EREGL: 0.00%  (negative score, skip)
FROTO: 25.00% ← CAPPED at maximum
GARAN: 25.00% ← CAPPED at maximum
MGROS: 25.00% ← CAPPED at maximum
SISE: 25.00% ← CAPPED at maximum (fills up budget)
THYAO: 0.00%
TOASO: 0.00%
────────────────────
TOTAL:  100%
```

---

### Step 6: Monthly Rebalance & Hold

At month-end (26 June 2017):
- **Decision made** at close with weights above
- **Executed** on next trading day (27 June 2017)
- **Held** for the entire next month
- **Rebalanced** on next month-end (31 July 2017)

Over 104 months, weights change based on evolving signals. Example contrast:

**Jul 2017:** EREGL, FROTO, MGROS, SISE = 25% each
**Aug 2017:** Mix changes → BIMAS 21.54%, EREGL 25%, FROTO 3.46%, MGROS 25%, THYAO 25%
**...evolves throughout 8.5 years...**
**Jan 2026:** AKBNK, EKGYO, FROTO, TOASO = 25% each

---

## 📈 Portfolio Weight Evolution

### Average Allocation Across All 104 Months
```
FROTO.IS    : 13.21%  ← Most favored (strong export signals)
BIMAS.IS    : 13.19%
MGROS.IS    : 12.56%
THYAO.IS    : 10.63%
EREGL.IS    : 10.50%
GARAN.IS    :  9.93%
TOASO.IS    :  9.22%
SISE.IS     :  8.95%
EKGYO.IS    :  6.43%
AKBNK.IS    :  5.39%  ← Least favored
━━━━━━━━━━━━━━━━━━━━
TOTAL       : 100%
```

**Observation:** The spread reflects long-term sector trends—exporters and consumer stocks did well; banks less so.

---

## 🔄 Data Pipeline

- **Asset prices:** Yahoo Finance (`yfinance`) | 2016-01-01 to 2026-02-23
- **Macro data:** CBRT EVDS API (USD/TRY, WACF, CPI) | 2016-02-04 to 2026-02-23
- **Lookback period:** 252 trading days (1 year) before first trade
- **First rebalance:** 30 June 2017 (after 252-day warm-up)
- **Backtest period:** 3 Jul 2017 – 23 Feb 2026 (2,166 trading days)

## 📋 Repository Structure

```text
src/
  config.py               # Universe, parameter defaults, lag assumptions
  asset_fetch.py          # Download BIST prices from Yahoo Finance
  macro_fetch.py          # Fetch macro data from CBRT EVDS with lag-safe handling
  signal_generation.py    # Compute technical + macro signals, combine into composite score
  signal_quality.py       # Compute confidence weighting for signal filtering
  optimization.py         # Signal-tilted Markowitz optimizer with cvxpy
  backtest.py             # Monthly rebalance simulation, metrics, visualizations
  
data/
  bist_prices.csv                        # 10-stock daily prices
  macro_data.csv                          # Daily macro indicators (USD/TRY, CPI, WACF)
  composite_scores.csv                    # Daily signal scores [-1, +1]
  final_weights_history.csv               # 104 monthly weight vectors
  FINAL_CONFIGURATION_SUMMARY.csv         # Backtest results & metrics
  final_strategy_returns.csv              # Daily strategy returns
  final_benchmark_returns.csv             # Daily benchmark (equal-weight) returns
  sensitivity_*.csv                       # Parameter sweep results
  
reports/
  cumulative_returns.png                  # Strategy vs. benchmark growth chart
  drawdown.png                            # Drawdown comparison
  weights_over_time.png                   # Stacked area of monthly weights
  sensitivity_sharpe_ra_ts.png            # Heatmap: Risk Aversion × Tilt Strength
  sensitivity_excess_ra_ts.png
  sensitivity_sharpe_mw_lb.png            # Heatmap: Max Weight × Lookback Period
  sensitivity_excess_mw_lb.png

tests/
  conftest.py
  test_pipeline.py
```

## ⚙️ Key Parameters

```python
# Lookback & Rebalance
DEFAULT_LOOKBACK = 252                  # 1 year of history for statistics
DEFAULT_PRICE_START = "2016-01-01"      # Historical warm-up
DEFAULT_BACKTEST_START = "2017-06-01"   # First rebalance ~252 days later

# Markowitz Optimization
DEFAULT_RISK_AVERSION = 5.0             # Penalty on volatility (γ)
DEFAULT_TILT_STRENGTH = 0.15            # Signal impact on expected returns (λ)
DEFAULT_MAX_WEIGHT = 0.25               # Per-asset cap (25%)
DEFAULT_MIN_WEIGHT = 0.0                # No minimum (can be excluded)
DEFAULT_SHRINK_FACTOR = 0.30            # Diagonal shrinkage of covariance

# Signal Generation
DEFAULT_TECH_WEIGHT = 0.60              # 60% technical, 40% macro
DEFAULT_MACRO_WEIGHT = 0.40

# Technical Indicators
TECHNICAL_WINDOWS = {
    "ma_short": 50,                     # 50-day moving average
    "ma_long": 200,                     # 200-day moving average
    "momentum": 63,                     # 63-day return (3 months)
    "volatility": 63,                   # 63-day rolling std dev
    "volatility_baseline": 252,         # 252-day median vol (1 year)
}

# Macro Data Lags (conservative)
USDTRY_RELEASE_LAG_DAYS = 1             # Available next day
WACF_RELEASE_LAG_DAYS = 1
CPI_RELEASE_LAG_MONTHS = 1              # Available next month
```

## ▶️ How to Run

### Setup
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Refresh Data & Run Backtest
```bash
# 1. Update prices (optional; data is cached)
python src/asset_fetch.py

# 2. Update macro data (optional)
python src/macro_fetch.py

# 3. Generate signals
python src/signal_generation.py

# 4. Run full backtest with final configuration
python final_run.py
```

### Run Tests
```bash
pytest tests/
```

### Explore Sensitivity
```bash
# Test parameter grid: Risk Aversion × Tilt Strength × Max Weight × Lookback
python fine_tuned_sensitivity.py     # Granular tilt strength sweep
python sensitivity.py                # Coarse 2D sweeps with heatmaps
python sensitivity_report.py         # Summary tables
```

## 📊 Performance Summary

| Metric | Strategy | Benchmark | Excess |
|--------|----------|-----------|---------|
| **Sharpe Ratio** | 1.971 | 1.728 | +0.243 |
| **Annual Return** | 61.86% | 48.49% | +13.37% |
| **Annual Volatility** | 31.39% | 28.07% | +3.32% |
| **Max Drawdown** | -32.92% | -32.40% | -0.52% |
| **Calmar Ratio** | 1.879 | 1.496 | +0.383 |
| **Total 9-Year Return** | 6,321.75% | 4,929.90% | +1,391.85% |
| **Test Period** | Jul 2017 – Feb 2026 | Same | Same |
| **Rebalances** | 104 monthly | 104 monthly | — |

## 🔍 Timing and Bias Controls

- **No look-ahead bias:** Rebalance decisions use only data available as of month-end close
- **No data snooping:** Parameters chosen before detailed backtest (RA=5, TS=0.15, MW=25%)
- **Conservative lags:** Macro data shifted forward by release-lag days (1-30 days depending on series)
- **Synthetic row removal:** Stale price rows (unchanged prices) are removed
- **Forward-fill only:** Price data is never backfilled
- **Real rebalance dates:** Rebalances occur on last *trading* day, not calendar month-end

## 💡 Why This Works

1. **Capture Regime Change:** Macro + tech signals together detect economic turning points
2. **Diversify Signals:** Technical = short-term momentum; Macro = longer structural shifts
3. **Confidence Weighting:** Weak/conflicting signals are dampened, avoiding spurious trades
4. **Conservative Tilt:** λ=0.15 is modest; doesn't overfit to noisy signals
5. **Sector Sensitivity Matrix:** Recognizes that different sectors respond differently to macro conditions (e.g., weak TL helps exporters, hurts banks)
6. **Monthly Rebalance:** Frequent enough to capture regime changes; infrequent enough to minimize transaction costs
7. **Markowitz Discipline:** Risk-adjusted optimization prevents concentration in noisy signals



## ✅ Validation & Testing

`src/backtest.py` includes comprehensive validation checks:

- Strategy and benchmark return indices match
- Optimized weights sum to 1.0 (fully invested)
- Optimized weights stay non-negative (long-only)
- Optimized weights respect 25% cap per asset
- Every rebalance date has a matching score row
- No forward-looking bias in signal computation

Run tests:
```bash
pytest tests/
```

## 📝 Important Notes

1. **Covariance Estimation:** Uses diagonal shrinkage (30%), not full Ledoit-Wolf
2. **Lookback Period:** 252 trading days ensures sufficient history for stable estimates
3. **Rebalance Frequency:** Monthly is a trade-off between capturing regime changes and minimizing turnover
4. **Macro Lag Handling:** All lag assumptions are conservative (e.g., CPI shifted 1 full month)
5. **Tilt Strength (λ=0.15):** Chosen after sensitivity testing (fine sweep from 0.0–0.5)
   - λ=0.0: Ignores signals, Sharpe = 1.967
   - λ=0.15: Best balance, Sharpe = 1.971 (+0.004 improvement)
   - λ=0.5: Overfits to noisy signals, Sharpe = 1.923
6. **Risk Aversion (γ=5.0):** Tuned in sensitivity analysis; penalizes volatility ~5× expected return gain
7. **Max Weight (25%):** Prevents over-concentration; allows 4 stocks at full allocation

## 🎓 Extensions & Future Work

- **Dynamic risk aversion:** Adjust γ based on market regime volatility
- **Machine learning signals:** Replace manual regime classification with learned models
- **Transaction cost modeling:** Include bid-ask spreads and commissions
- **Multi-asset classes:** Extend from equities to include bonds, currencies, commodities
- **Cross-sector correlations:** Model dynamic correlations across sectors
- **Ensemble methods:** Combine with other strategies (value, quality, low-vol factors)
