# YAP 471 - Dynamic Sector and Asset Rotation with Markowitz Optimization

Computational Finance term project. A hybrid signal-driven portfolio strategy on Borsa Istanbul (BIST) equities using Markowitz Mean-Variance optimization.

**Team:** Emirhan Yavuz, Aylin Barutcu, Bilgehan Tekin, Utku Kaya

## Strategy Overview

1. **Signal Generation** — Composite score (-1 to +1) per asset combining:
   - *Technical:* 50/200-day MA trend, 63-day momentum (cross-sectional z-score), volatility regime
   - *Macro:* Interest rate regime (WACF), inflation regime (CPI YoY), FX regime (USD/TRY) with sector-specific sensitivity weights

2. **Portfolio Optimization** — Markowitz mean-variance with signal-tilted inputs:
   - Expected returns tilted by composite score
   - Covariance matrix adjusted via Ledoit-Wolf shrinkage + signal-based vol scaling
   - Constraints: fully invested, long-only, max 25% per asset

3. **Backtesting** — Monthly rebalance, benchmark: 1/N equal-weight portfolio

## Asset Universe (4 Sectors, 10 Stocks)

| Sector | Tickers |
|--------|---------|
| Mining/Industrial | EREGL, SISE |
| Export-Oriented | TOASO, FROTO, THYAO |
| Interest-Sensitive | GARAN, AKBNK, EKGYO |
| Defensive/Retail | BIMAS, MGROS |

## Data Sources

- **Stock Prices:** Yahoo Finance (`yfinance`), daily, 2016-2026
- **Macro Data:** TCMB EVDS API — USD/TRY, CPI index, WACF interest rate

## Project Structure

```
src/
  asset_fetch.py          # BIST price data fetcher (yfinance)
  macro_fetch.py          # EVDS macro data fetcher (CPI, rates, FX)
  signal_generation.py    # Technical + macro hybrid signal engine
  optimization.py         # Markowitz MV optimizer (cvxpy)
  backtest.py             # Monthly rebalance simulation & reporting

data/
  bist_prices.csv         # Daily close prices (10 tickers)
  macro_data.csv          # Daily macro panel (USDTRY, CPI_YOY, WACF_RATE)
  composite_scores.csv    # Signal scores per asset
  backtest_metrics.csv    # Performance comparison table

reports/
  cumulative_returns.png  # Strategy vs benchmark growth chart
  drawdown.png            # Drawdown comparison
  weights_over_time.png   # Portfolio allocation over time

docs/
  471_proposal (2).pdf    # Original project proposal
```

## Quick Start

```bash
# Install dependencies
pip install yfinance pandas numpy scipy cvxpy matplotlib evds

# Fetch data
python src/asset_fetch.py
python src/macro_fetch.py

# Run full backtest
python src/backtest.py
```

## Results (June 2017 - February 2026)

| Metric | Strategy | Benchmark (1/N) |
|--------|----------|-----------------|
| Total Return | 6,360% | 2,949% |
| Ann. Return | 62.0% | 48.5% |
| Ann. Volatility | 31.2% | 27.9% |
| Sharpe Ratio | 1.99 | 1.74 |
| Max Drawdown | -32.4% | -32.4% |
| Calmar Ratio | 1.91 | 1.50 |
