"""
Backtesting & Reporting Module
==============================
Monthly rebalance simulation comparing:
  - Strategy: Markowitz + hybrid signal
  - Benchmark: 1/N equal-weight portfolio

Outputs: cumulative returns, performance metrics, visualisations.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

from asset_fetch import load_prices
from macro_fetch import load_macro
from signal_generation import compute_composite_scores
from optimization import compute_weights, equal_weight

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
REPORTS_DIR = PROJECT_ROOT / "reports"
REPORTS_DIR.mkdir(exist_ok=True)


# ═══════════════════════════════════════════════════════════════════════════
#  Backtest engine
# ═══════════════════════════════════════════════════════════════════════════

def get_rebalance_dates(prices: pd.DataFrame, freq: str = "M") -> list[pd.Timestamp]:
    """Get month-end rebalance dates from the price index."""
    return list(prices.resample(freq).last().dropna().index)


def run_backtest(
    prices: pd.DataFrame,
    scores: pd.DataFrame,
    risk_aversion: float = 5.0,
    tilt_strength: float = 0.5,
    max_weight: float = 0.25,
    lookback: int = 252,
    start_date: str = "2017-01-01",
) -> dict:
    """Run monthly-rebalanced backtest for strategy and benchmark.

    Parameters
    ----------
    start_date : first allowed rebalance date (needs enough history for lookback)

    Returns
    -------
    dict with keys: strategy_returns, benchmark_returns, weights_history
    """
    daily_returns = prices.pct_change(fill_method=None).dropna()

    # Filter rebalance dates
    rebal_dates = get_rebalance_dates(prices)
    rebal_dates = [d for d in rebal_dates if d >= pd.Timestamp(start_date)]

    n_assets = len(prices.columns)
    w_eq = equal_weight(n_assets)

    # Storage
    strat_daily = []
    bench_daily = []
    weights_hist = []

    for i, rebal_date in enumerate(rebal_dates[:-1]):
        next_rebal = rebal_dates[i + 1]

        # Compute optimized weights
        w_opt = compute_weights(
            prices, scores, rebal_date,
            lookback=lookback,
            risk_aversion=risk_aversion,
            tilt_strength=tilt_strength,
            max_weight=max_weight,
        )
        weights_hist.append(w_opt)

        # Daily returns in holding period
        mask = (daily_returns.index > rebal_date) & (daily_returns.index <= next_rebal)
        period_rets = daily_returns.loc[mask]

        if period_rets.empty:
            continue

        # Portfolio daily returns
        strat_period = (period_rets.values @ w_opt.values)
        bench_period = (period_rets.values @ w_eq)

        for j, dt in enumerate(period_rets.index):
            strat_daily.append((dt, strat_period[j]))
            bench_daily.append((dt, bench_period[j]))

    # Build return series
    strat_ret = pd.Series(
        dict(strat_daily), name="Strategy"
    ).sort_index()
    bench_ret = pd.Series(
        dict(bench_daily), name="Benchmark_1N"
    ).sort_index()

    weights_df = pd.DataFrame(weights_hist)

    return {
        "strategy_returns": strat_ret,
        "benchmark_returns": bench_ret,
        "weights_history": weights_df,
    }


# ═══════════════════════════════════════════════════════════════════════════
#  Performance metrics
# ═══════════════════════════════════════════════════════════════════════════

def performance_metrics(returns: pd.Series, name: str = "") -> pd.Series:
    """Compute standard performance metrics."""
    cum = (1 + returns).cumprod()
    total_ret = cum.iloc[-1] - 1
    n_years = (returns.index[-1] - returns.index[0]).days / 365.25
    ann_ret = (1 + total_ret) ** (1 / n_years) - 1
    ann_vol = returns.std() * np.sqrt(252)
    sharpe = ann_ret / ann_vol if ann_vol > 0 else 0

    # Max drawdown
    rolling_max = cum.cummax()
    drawdown = (cum - rolling_max) / rolling_max
    max_dd = drawdown.min()

    # Calmar ratio
    calmar = ann_ret / abs(max_dd) if max_dd != 0 else 0

    return pd.Series({
        "Total Return (%)": round(total_ret * 100, 2),
        "Ann. Return (%)": round(ann_ret * 100, 2),
        "Ann. Volatility (%)": round(ann_vol * 100, 2),
        "Sharpe Ratio": round(sharpe, 3),
        "Max Drawdown (%)": round(max_dd * 100, 2),
        "Calmar Ratio": round(calmar, 3),
        "# Trading Days": len(returns),
    }, name=name)


# ═══════════════════════════════════════════════════════════════════════════
#  Visualisation
# ═══════════════════════════════════════════════════════════════════════════

def plot_cumulative_returns(strat_ret, bench_ret, save_path=None):
    """Plot cumulative returns for strategy vs benchmark."""
    cum_strat = (1 + strat_ret).cumprod()
    cum_bench = (1 + bench_ret).cumprod()

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(cum_strat.index, cum_strat.values, label="Strategy (Markowitz + Signals)", linewidth=2)
    ax.plot(cum_bench.index, cum_bench.values, label="Benchmark (1/N Equal Weight)", linewidth=2, linestyle="--")
    ax.set_title("Cumulative Returns: Strategy vs Benchmark", fontsize=14)
    ax.set_xlabel("Date")
    ax.set_ylabel("Growth of 1 TRY")
    ax.legend(fontsize=12)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150)
        print(f"Saved -> {save_path}")
    plt.close(fig)
    return fig


def plot_drawdown(strat_ret, bench_ret, save_path=None):
    """Plot drawdown curves."""
    fig, ax = plt.subplots(figsize=(12, 4))

    for ret, label, ls in [(strat_ret, "Strategy", "-"), (bench_ret, "Benchmark", "--")]:
        cum = (1 + ret).cumprod()
        dd = (cum - cum.cummax()) / cum.cummax() * 100
        ax.fill_between(dd.index, dd.values, alpha=0.3, label=label, linestyle=ls)

    ax.set_title("Drawdown (%)", fontsize=14)
    ax.set_xlabel("Date")
    ax.set_ylabel("Drawdown %")
    ax.legend(fontsize=12)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150)
        print(f"Saved -> {save_path}")
    plt.close(fig)
    return fig


def plot_weights_over_time(weights_df, save_path=None):
    """Stacked area chart of portfolio weights over time."""
    fig, ax = plt.subplots(figsize=(12, 6))
    # Clean column names (remove .IS suffix for readability)
    cols_clean = [c.replace(".IS", "") for c in weights_df.columns]
    weights_df.columns = cols_clean
    weights_df.plot.area(ax=ax, stacked=True, alpha=0.8)
    ax.set_title("Portfolio Weights Over Time", fontsize=14)
    ax.set_xlabel("Rebalance Date")
    ax.set_ylabel("Weight")
    ax.legend(loc="center left", bbox_to_anchor=(1.0, 0.5), fontsize=9)
    ax.set_ylim(0, 1)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150)
        print(f"Saved -> {save_path}")
    plt.close(fig)
    return fig


# ═══════════════════════════════════════════════════════════════════════════
#  Main
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("Loading data ...")
    prices = load_prices()
    macro = load_macro()

    print("Computing signals ...")
    scores = compute_composite_scores(prices, macro)

    print("Running backtest ...")
    results = run_backtest(prices, scores, start_date="2017-06-01")

    strat_ret = results["strategy_returns"]
    bench_ret = results["benchmark_returns"]
    weights_df = results["weights_history"]

    # ── Performance table ──
    strat_metrics = performance_metrics(strat_ret, name="Strategy")
    bench_metrics = performance_metrics(bench_ret, name="Benchmark (1/N)")

    report = pd.DataFrame([strat_metrics, bench_metrics])
    print("\n" + "=" * 60)
    print("  BACKTEST RESULTS")
    print("=" * 60)
    print(report.to_string())
    print("=" * 60)

    # Save metrics
    report.to_csv(DATA_DIR / "backtest_metrics.csv")

    # ── Plots ──
    plot_cumulative_returns(strat_ret, bench_ret, REPORTS_DIR / "cumulative_returns.png")
    plot_drawdown(strat_ret, bench_ret, REPORTS_DIR / "drawdown.png")
    plot_weights_over_time(weights_df, REPORTS_DIR / "weights_over_time.png")

    print("\nDone! Check reports/ folder for plots.")
