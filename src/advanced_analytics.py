"""
Advanced Analytics & Visualisation Module
==========================================
Rolling Sharpe, monthly heatmap, sector attribution, XU100 benchmark.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import yfinance as yf

from config import DATA_DIR, REPORTS_DIR, SECTORS


# ═══════════════════════════════════════════════════════════════════════════
#  1. Rolling Sharpe ratio (1-year window)
# ═══════════════════════════════════════════════════════════════════════════

def plot_rolling_sharpe(
    strat_ret: pd.Series,
    bench_ret: pd.Series,
    window: int = 252,
    save_path=None,
) -> plt.Figure:
    """Plot 1-year rolling Sharpe ratio for strategy vs benchmark."""
    def _rolling_sharpe(returns, win):
        roll_mean = returns.rolling(win).mean() * 252
        roll_std = returns.rolling(win).std() * np.sqrt(252)
        return (roll_mean / roll_std).replace([np.inf, -np.inf], np.nan)

    rs_strat = _rolling_sharpe(strat_ret, window)
    rs_bench = _rolling_sharpe(bench_ret, window)

    fig, ax = plt.subplots(figsize=(13, 5))
    ax.plot(rs_strat.index, rs_strat.values, label="Strategy", linewidth=2, color="#1f77b4")
    ax.plot(rs_bench.index, rs_bench.values, label="Benchmark (1/N)", linewidth=2,
            linestyle="--", color="#ff7f0e")
    ax.axhline(0, color="grey", linewidth=0.8, linestyle=":")
    ax.fill_between(rs_strat.index, rs_strat.values, rs_bench.values,
                    where=rs_strat.values >= rs_bench.values,
                    alpha=0.15, color="#1f77b4", label="Strategy outperforms")
    ax.fill_between(rs_strat.index, rs_strat.values, rs_bench.values,
                    where=rs_strat.values < rs_bench.values,
                    alpha=0.15, color="#ff7f0e", label="Benchmark outperforms")
    ax.set_title(f"Rolling Sharpe Ratio ({window}-day window)", fontsize=14)
    ax.set_xlabel("Date")
    ax.set_ylabel("Sharpe Ratio")
    ax.legend(fontsize=10, loc="best")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150)
        print(f"Saved -> {save_path}")
    plt.close(fig)
    return fig


# ═══════════════════════════════════════════════════════════════════════════
#  2. Monthly returns heatmap with excess return panel
# ═══════════════════════════════════════════════════════════════════════════

def _monthly_returns_table(returns: pd.Series) -> pd.DataFrame:
    """Pivot daily returns into a Year×Month table of monthly total returns (%)."""
    monthly = returns.resample("ME").apply(lambda x: (1 + x).prod() - 1) * 100
    tbl = monthly.to_frame("ret")
    tbl["Year"] = tbl.index.year
    tbl["Month"] = tbl.index.month
    return tbl.pivot(index="Year", columns="Month", values="ret")


def plot_monthly_heatmap(
    strat_ret: pd.Series,
    bench_ret: pd.Series,
    save_path=None,
) -> plt.Figure:
    """Side-by-side heatmaps: strategy monthly returns and excess returns."""
    strat_tbl = _monthly_returns_table(strat_ret)
    bench_tbl = _monthly_returns_table(bench_ret)
    excess_tbl = strat_tbl - bench_tbl

    month_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    fig, axes = plt.subplots(1, 2, figsize=(20, max(6, len(strat_tbl) * 0.55)),
                             sharey=True)

    vmax_s = max(abs(strat_tbl.max().max()), abs(strat_tbl.min().min()))
    sns.heatmap(strat_tbl, annot=True, fmt=".1f", center=0,
                cmap="RdYlGn", vmin=-vmax_s, vmax=vmax_s,
                xticklabels=month_labels, linewidths=0.5,
                ax=axes[0], cbar_kws={"label": "Return (%)"})
    axes[0].set_title("Strategy Monthly Returns (%)", fontsize=13)
    axes[0].set_ylabel("Year")

    vmax_e = max(abs(excess_tbl.max().max()), abs(excess_tbl.min().min()))
    sns.heatmap(excess_tbl, annot=True, fmt=".1f", center=0,
                cmap="RdYlGn", vmin=-vmax_e, vmax=vmax_e,
                xticklabels=month_labels, linewidths=0.5,
                ax=axes[1], cbar_kws={"label": "Excess (%)"})
    axes[1].set_title("Excess Returns: Strategy − Benchmark (%)", fontsize=13)

    fig.suptitle("Monthly Returns Heatmap", fontsize=15, y=1.01)
    fig.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"Saved -> {save_path}")
    plt.close(fig)
    return fig


# ═══════════════════════════════════════════════════════════════════════════
#  3. Sector-level return attribution
# ═══════════════════════════════════════════════════════════════════════════

TICKER_SECTOR = {
    ticker: sector
    for sector, tickers in SECTORS.items()
    for ticker in tickers
}


def compute_sector_attribution(
    prices: pd.DataFrame,
    weights_df: pd.DataFrame,
    rebalance_dates: list[pd.Timestamp],
) -> pd.DataFrame:
    """Decompose portfolio return into sector-level contributions.

    For each rebalance period, strategy return = sum of (w_i * r_i).
    We group w_i * r_i by sector to get sector contributions.
    """
    daily_returns = prices.pct_change(fill_method=None).dropna()

    records = []
    for i in range(len(rebalance_dates) - 1):
        start = rebalance_dates[i]
        end = rebalance_dates[i + 1]
        mask = (daily_returns.index > start) & (daily_returns.index <= end)
        period_rets = daily_returns.loc[mask]

        if period_rets.empty or start not in weights_df.index:
            continue

        w = weights_df.loc[start]
        # cum period return per asset
        asset_cum = (1 + period_rets).prod() - 1
        contrib = w * asset_cum  # weighted contribution

        sector_contrib = {}
        for sector in SECTORS:
            tickers_in = [t for t in SECTORS[sector] if t in contrib.index]
            sector_contrib[sector] = contrib[tickers_in].sum()
        sector_contrib["_period_end"] = end
        records.append(sector_contrib)

    attr = pd.DataFrame(records)
    attr.index = pd.to_datetime(attr.pop("_period_end"))
    attr.index.name = "Date"
    return attr


def plot_sector_attribution(
    attr_df: pd.DataFrame,
    save_path=None,
) -> plt.Figure:
    """Stacked bar chart of sector contributions to portfolio return."""
    plot_df = attr_df * 100  # convert to %

    colors = ["#4e79a7", "#f28e2b", "#e15759", "#76b7b2"]
    fig, ax = plt.subplots(figsize=(14, 6))
    plot_df.plot.bar(stacked=True, ax=ax, color=colors, width=0.8, edgecolor="white",
                     linewidth=0.3)

    ax.set_title("Sector Return Attribution per Rebalance Period (%)", fontsize=14)
    ax.set_ylabel("Contribution to Return (%)")
    ax.set_xlabel("Period End Date")

    # Simplify x-axis labels
    tick_labels = [d.strftime("%Y-%m") for d in plot_df.index]
    ax.set_xticklabels(tick_labels, rotation=45, ha="right", fontsize=7)

    # Show every Nth label to avoid clutter
    n_labels = len(tick_labels)
    step = max(1, n_labels // 20)
    for i, label in enumerate(ax.xaxis.get_ticklabels()):
        if i % step != 0:
            label.set_visible(False)

    ax.axhline(0, color="black", linewidth=0.5)
    ax.legend(loc="upper left", fontsize=9, framealpha=0.9)
    ax.grid(True, alpha=0.2, axis="y")
    fig.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"Saved -> {save_path}")
    plt.close(fig)
    return fig


# ═══════════════════════════════════════════════════════════════════════════
#  4. XU100 (BIST-100 index) benchmark comparison
# ═══════════════════════════════════════════════════════════════════════════

def fetch_xu100(start: str, end: str) -> pd.Series:
    """Download BIST-100 index daily closes from Yahoo Finance."""
    raw = yf.download("XU100.IS", start=start, end=end, auto_adjust=True, progress=False)
    if raw.empty:
        raise ValueError("Could not download XU100.IS from Yahoo Finance.")
    series = raw["Close"].squeeze()
    series.name = "XU100"
    series.index = series.index.tz_localize(None)
    return series


def plot_xu100_comparison(
    strat_ret: pd.Series,
    bench_ret: pd.Series,
    xu100_prices: pd.Series | None = None,
    save_path=None,
) -> plt.Figure:
    """Overlay strategy, 1/N benchmark, and XU100 cumulative returns."""
    if xu100_prices is None:
        xu100_prices = fetch_xu100(
            start=str(strat_ret.index[0].date()),
            end=str(strat_ret.index[-1].date()),
        )

    # Align XU100 to strategy dates
    xu100_aligned = xu100_prices.reindex(strat_ret.index, method="ffill")
    xu100_ret = xu100_aligned.pct_change().dropna()

    # Common start
    common_start = max(strat_ret.index[0], xu100_ret.index[0])
    strat_ret_c = strat_ret.loc[common_start:]
    bench_ret_c = bench_ret.loc[common_start:]
    xu100_ret_c = xu100_ret.loc[common_start:]

    cum_strat = (1 + strat_ret_c).cumprod()
    cum_bench = (1 + bench_ret_c).cumprod()
    cum_xu100 = (1 + xu100_ret_c).cumprod()

    fig, ax = plt.subplots(figsize=(13, 6))
    ax.plot(cum_strat.index, cum_strat.values, label="Strategy (Markowitz + Signals)",
            linewidth=2, color="#1f77b4")
    ax.plot(cum_bench.index, cum_bench.values, label="Benchmark (1/N Equal Weight)",
            linewidth=2, linestyle="--", color="#ff7f0e")
    ax.plot(cum_xu100.index, cum_xu100.values, label="XU100 (BIST-100 Index)",
            linewidth=2, linestyle="-.", color="#2ca02c")
    ax.set_title("Cumulative Returns: Strategy vs 1/N vs XU100", fontsize=14)
    ax.set_xlabel("Date")
    ax.set_ylabel("Growth of 1 TRY")
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150)
        print(f"Saved -> {save_path}")
    plt.close(fig)
    return fig


# ═══════════════════════════════════════════════════════════════════════════
#  CLI
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).parent))

    from asset_fetch import load_prices
    from backtest import run_backtest, performance_metrics
    from macro_fetch import get_macro_panel
    from signal_generation import compute_composite_scores

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
    rebal_dates = results["rebalance_dates"]

    # 1. Rolling Sharpe
    print("\n[1/4] Rolling Sharpe ratio ...")
    plot_rolling_sharpe(strat_ret, bench_ret, save_path=REPORTS_DIR / "rolling_sharpe.png")

    # 2. Monthly heatmap
    print("[2/4] Monthly returns heatmap ...")
    plot_monthly_heatmap(strat_ret, bench_ret, save_path=REPORTS_DIR / "monthly_heatmap.png")

    # 3. Sector attribution
    print("[3/4] Sector attribution ...")
    attr = compute_sector_attribution(prices, weights_df, rebal_dates)
    attr.to_csv(DATA_DIR / "sector_attribution.csv")
    plot_sector_attribution(attr, save_path=REPORTS_DIR / "sector_attribution.png")

    # 4. XU100 comparison
    print("[4/4] XU100 benchmark ...")
    try:
        plot_xu100_comparison(strat_ret, bench_ret, save_path=REPORTS_DIR / "xu100_comparison.png")
    except Exception as exc:
        print(f"  XU100 download failed ({exc}). Skipping XU100 plot.")

    print("\nAdvanced analytics complete! Check reports/ folder.")
