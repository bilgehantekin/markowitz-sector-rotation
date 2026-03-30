"""
Backtesting & Reporting Module
==============================
Monthly rebalance simulation for the strategy and equal-weight benchmark.
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from typing import Union, List, Dict

from asset_fetch import load_prices
from config import (
    DATA_DIR,
    DEFAULT_BACKTEST_START,
    DEFAULT_LOOKBACK,
    DEFAULT_MAX_WEIGHT,
    DEFAULT_RISK_AVERSION,
    DEFAULT_TILT_STRENGTH,
    METRICS_FILENAME,
    REPORTS_DIR,
    WEIGHTS_FILENAME,
)
from macro_fetch import get_macro_panel
from optimization import compute_weights, equal_weight, validate_weight_vector
from signal_generation import compute_composite_scores


# ═══════════════════════════════════════════════════════════════════════════
#  Backtest engine
# ═══════════════════════════════════════════════════════════════════════════

def get_rebalance_dates(index_like: Union[pd.DataFrame, pd.DatetimeIndex]) -> List[pd.Timestamp]:
    """Get the last tradable date in each month from an existing trading index."""
    index = index_like.index if isinstance(index_like, pd.DataFrame) else pd.DatetimeIndex(index_like)
    index = pd.DatetimeIndex(index).sort_values().unique()
    grouped = index.to_series(index=index).groupby(index.to_period("M")).last()
    return list(grouped.to_list())


def run_backtest(
    prices: pd.DataFrame,
    scores: pd.DataFrame,
    risk_aversion: float = DEFAULT_RISK_AVERSION,
    tilt_strength: float = DEFAULT_TILT_STRENGTH,
    max_weight: float = DEFAULT_MAX_WEIGHT,
    lookback: int = DEFAULT_LOOKBACK,
    start_date: str = DEFAULT_BACKTEST_START,
    cost_bps: float = 0.0,
) -> dict:
    """Run a monthly-rebalanced backtest for strategy and benchmark.

    Parameters
    ----------
    cost_bps : float
        Round-trip transaction cost in basis points (e.g. 30 = 0.30%).
        Applied proportionally to turnover at each rebalance.
    """
    daily_returns = prices.pct_change(fill_method=None).dropna()
    signal_index = prices.index.intersection(scores.index)
    rebal_dates = get_rebalance_dates(signal_index)
    rebal_dates = [d for d in rebal_dates if d >= pd.Timestamp(start_date)]
    if len(rebal_dates) < 2:
        raise ValueError("Not enough rebalance dates to run the backtest.")

    n_assets = len(prices.columns)
    w_eq = equal_weight(n_assets)
    cost_frac = cost_bps / 10_000  # convert bps to fraction

    strat_daily = []
    bench_daily = []
    weights_hist = []
    turnover_hist = []
    w_prev = None

    for i, rebal_date in enumerate(rebal_dates[:-1]):
        next_rebal = rebal_dates[i + 1]

        w_opt = compute_weights(
            prices, scores, rebal_date,
            lookback=lookback,
            risk_aversion=risk_aversion,
            tilt_strength=tilt_strength,
            max_weight=max_weight,
        )
        weights_hist.append(w_opt.rename(rebal_date))

        # Transaction cost: turnover = half the sum of absolute weight changes
        if w_prev is not None:
            turnover = np.abs(w_opt.values - w_prev).sum() / 2
        else:
            turnover = np.abs(w_opt.values - w_eq).sum() / 2  # vs initial equal-weight
        turnover_hist.append((rebal_date, turnover))
        w_prev = w_opt.values.copy()

        mask = (daily_returns.index > rebal_date) & (daily_returns.index <= next_rebal)
        period_rets = daily_returns.loc[mask]

        if period_rets.empty:
            continue

        strat_period = period_rets.values @ w_opt.values
        bench_period = period_rets.values @ w_eq

        # Deduct transaction cost from the first day of the holding period
        if cost_frac > 0:
            strat_period[0] -= cost_frac * turnover

        for j, dt in enumerate(period_rets.index):
            strat_daily.append((dt, strat_period[j]))
            bench_daily.append((dt, bench_period[j]))

    strat_ret = pd.Series(dict(strat_daily), name="Strategy").sort_index()
    bench_ret = pd.Series(dict(bench_daily), name="Benchmark_1N").sort_index()
    bench_ret = bench_ret.reindex(strat_ret.index)

    weights_df = pd.DataFrame(weights_hist)

    turnover_series = pd.Series(dict(turnover_hist), name="Turnover")

    return {
        "strategy_returns": strat_ret,
        "benchmark_returns": bench_ret,
        "weights_history": weights_df,
        "rebalance_dates": rebal_dates,
        "turnover_history": turnover_series,
        "cost_bps": cost_bps,
        "total_turnover": float(turnover_series.sum()),
        "total_cost_bps": float(turnover_series.sum() * cost_bps),
    }


# ═══════════════════════════════════════════════════════════════════════════
#  Performance metrics
# ═══════════════════════════════════════════════════════════════════════════

def performance_metrics(returns: pd.Series, name: str = "") -> pd.Series:
    """Compute standard performance metrics."""
    if returns.empty:
        raise ValueError(f"Cannot compute performance metrics for empty series: {name}")

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


def validate_weights_history(
    weights_df: pd.DataFrame,
    max_weight: float = DEFAULT_MAX_WEIGHT,
) -> pd.DataFrame:
    """Validate every rebalance weight vector against portfolio constraints."""
    records = []
    for date, row in weights_df.iterrows():
        result = validate_weight_vector(row, max_weight=max_weight)
        records.append(pd.Series(result, name=date))
    return pd.DataFrame(records)


def validate_backtest_results(
    results: dict,
    scores: pd.DataFrame,
    max_weight: float = DEFAULT_MAX_WEIGHT,
) -> Dict[str, bool]:
    """Run core sanity checks for a completed backtest."""
    weights_df = results["weights_history"]
    validation_df = validate_weights_history(weights_df, max_weight=max_weight)

    return {
        "matching_return_index": bool(
            results["strategy_returns"].index.equals(results["benchmark_returns"].index)
        ),
        "weights_sum_to_one": bool(validation_df["sum_to_one"].all()),
        "weights_non_negative": bool(validation_df["non_negative"].all()),
        "weights_within_cap": bool(validation_df["within_cap"].all()),
        "rebalance_dates_have_scores": bool(weights_df.index.isin(scores.index).all()),
    }


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
        ax.plot(dd.index, dd.values, label=label, linestyle=ls, linewidth=1.8)

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
    """Line chart of portfolio weights over time (one line per stock)."""
    fig, ax = plt.subplots(figsize=(14, 7))
    plot_df = weights_df.copy()
    plot_df.columns = [c.replace(".IS", "") for c in plot_df.columns]
    
    # Plot each stock as a separate line
    colors = plt.cm.tab10(np.linspace(0, 1, len(plot_df.columns)))
    for i, col in enumerate(plot_df.columns):
        ax.plot(plot_df.index, plot_df[col], marker='o', linewidth=2, 
                label=col, color=colors[i], markersize=4, alpha=0.8)
    
    ax.set_title("Portfolio Weights Over Time", fontsize=14, fontweight='bold')
    ax.set_xlabel("Rebalance Date", fontsize=12)
    ax.set_ylabel("Weight", fontsize=12)
    ax.legend(loc="best", ncol=2, fontsize=10, framealpha=0.95)
    ax.set_ylim(-0.02, max(0.30, plot_df.max().max() + 0.05))
    ax.grid(True, alpha=0.3, linestyle='--')
    
    # Improve x-axis readability
    fig.autofmt_xdate(rotation=45, ha='right')
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
    macro = get_macro_panel(prices.index)

    print("Computing signals ...")
    scores = compute_composite_scores(prices, macro)

    print("Running backtest ...")
    results = run_backtest(prices, scores)

    strat_ret = results["strategy_returns"]
    bench_ret = results["benchmark_returns"]
    weights_df = results["weights_history"]
    validation_flags = validate_backtest_results(results, scores)

    strat_metrics = performance_metrics(strat_ret, name="Strategy")
    bench_metrics = performance_metrics(bench_ret, name="Benchmark (1/N)")

    report = pd.DataFrame([strat_metrics, bench_metrics])
    print("\n" + "=" * 60)
    print("  BACKTEST RESULTS")
    print("=" * 60)
    print(report.to_string())
    print("=" * 60)

    print("\nValidation checks:")
    for name, passed in validation_flags.items():
        print(f"  {name}: {'PASS' if passed else 'FAIL'}")

    report.to_csv(DATA_DIR / METRICS_FILENAME)
    weights_df.to_csv(DATA_DIR / WEIGHTS_FILENAME)

    plot_cumulative_returns(strat_ret, bench_ret, REPORTS_DIR / "cumulative_returns.png")
    plot_drawdown(strat_ret, bench_ret, REPORTS_DIR / "drawdown.png")
    plot_weights_over_time(weights_df, REPORTS_DIR / "weights_over_time.png")

    print("\nDone! Check reports/ folder for plots.")
