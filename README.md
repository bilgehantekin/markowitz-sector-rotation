# YAP 471 - Dynamic BIST Rotation with Markowitz Optimization

Computational Finance term project implementing a proposal-faithful Borsa Istanbul rotation strategy. The system combines macro regime signals and technical indicators, then feeds the resulting composite score into a long-only Markowitz optimizer.

## What the project builds

- A 10-stock BIST universe across 4 sector groups:
  - Mining/Industrial: `EREGL.IS`, `SISE.IS`
  - Export-Oriented: `TOASO.IS`, `FROTO.IS`, `THYAO.IS`
  - Interest-Sensitive: `GARAN.IS`, `AKBNK.IS`, `EKGYO.IS`
  - Defensive/Retail: `BIMAS.IS`, `MGROS.IS`
- A hybrid regime score in `[-1, 1]` using:
  - Technical features: 50/200-day trend, 63-day momentum, volatility regime
  - Macro features: CPI YoY, WACF interest rate, USD/TRY
- A monthly rebalanced Markowitz portfolio with:
  - Fully invested budget constraint
  - Long-only weights
  - 25% max weight per asset
- A same-schedule equal-weight benchmark

## Data logic

- Asset prices come from Yahoo Finance via `yfinance`.
- Macro data comes from CBRT EVDS when an `EVDS_API_KEY` is available.
- If live EVDS access fails, the code falls back to cached macro data and migrates legacy cache files into the new lag-safe format.

## Timing and bias controls

- Synthetic non-trading price rows are removed if every asset price is unchanged from the prior day.
- Price data is forward-filled conservatively; no backfilling is used.
- USD/TRY and WACF are treated as available no earlier than the next trading day.
- CPI is shifted by one full month as a conservative release-lag proxy.
- Rebalance dates are the last tradable dates of each month, not calendar month-end labels.
- Portfolio weights decided at the rebalance close are applied starting on the next trading day.

## Repository structure

```text
src/
  config.py               # Shared paths, universe, defaults, lag assumptions
  asset_fetch.py          # Price download and cleaning
  macro_fetch.py          # EVDS fetch + lag-safe macro alignment
  signal_generation.py    # Technical + macro regime scoring
  optimization.py         # Signal-tilted Markowitz optimizer
  backtest.py             # Monthly simulation, metrics, plots, validation

tests/
  conftest.py
  test_pipeline.py

data/
  bist_prices.csv
  macro_data.csv
  composite_scores.csv
  backtest_metrics.csv
  weights_history.csv

reports/
  cumulative_returns.png
  drawdown.png
  weights_over_time.png
```

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Optional for live macro refresh:

```bash
export EVDS_API_KEY="your_api_key_here"
```

## How to run

Refresh price data:

```bash
python src/asset_fetch.py
```

Refresh or migrate macro data:

```bash
python src/macro_fetch.py
```

Generate composite scores:

```bash
python src/signal_generation.py
```

Run the full backtest:

```bash
python src/backtest.py
```

Run tests:

```bash
pytest
```

## Outputs

- `data/composite_scores.csv`: lag-safe regime scores by asset and date
- `data/backtest_metrics.csv`: strategy and benchmark performance metrics
- `data/weights_history.csv`: rebalance-date portfolio weights
- `reports/cumulative_returns.png`: growth of 1 TRY
- `reports/drawdown.png`: drawdown comparison
- `reports/weights_over_time.png`: stacked portfolio weights

## Important assumptions

- The covariance estimate uses diagonal shrinkage, not a true Ledoit-Wolf estimator.
- The default backtest start is June 1, 2017 so the technical indicators have enough warm-up history.
- Cached report files in the repo should be treated as generated artifacts; rerun the pipeline after code changes to reproduce current results.

## Validation expectations

`src/backtest.py` now checks and reports whether:

- strategy and benchmark return indices match
- optimized weights sum to 1
- optimized weights stay non-negative
- optimized weights stay within the 25% cap
- every rebalance date has a matching score row
