"""
Sensitivity Analysis Module
============================
Parameter sweeps and heatmap visualisation for robustness checks.
"""

import itertools
from typing import Sequence, Optional, Dict, List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from backtest import performance_metrics, run_backtest
from config import (
    DEFAULT_LOOKBACK,
    DEFAULT_MAX_WEIGHT,
    DEFAULT_RISK_AVERSION,
    DEFAULT_TILT_STRENGTH,
    REPORTS_DIR,
    DATA_DIR,
)


# ═══════════════════════════════════════════════════════════════════════════
#  Parameter sweep engine
# ═══════════════════════════════════════════════════════════════════════════

DEFAULT_GRIDS = {
    "risk_aversion": [1.0, 2.0, 3.0, 5.0, 8.0, 12.0],
    "tilt_strength": [0.0, 0.1, 0.25, 0.5, 0.75, 1.0],
    "max_weight": [0.15, 0.20, 0.25, 0.30, 0.40, 0.50],
    "lookback": [126, 189, 252, 378, 504],
}

PARAM_LABELS = {
    "risk_aversion": "Risk Aversion (γ)",
    "tilt_strength": "Tilt Strength (λ)",
    "max_weight": "Max Weight",
    "lookback": "Lookback (days)",
}


def run_sensitivity_sweep(
    prices: pd.DataFrame,
    scores: pd.DataFrame,
    param_x: str,
    values_x: Sequence,
    param_y: str,
    values_y: Sequence,
    fixed_params: Optional[Dict] = None,
) -> pd.DataFrame:
    """Run a 2-D parameter sweep and return Sharpe & excess Sharpe for each cell.

    Parameters
    ----------
    param_x, param_y : names matching run_backtest kwargs
    values_x, values_y : grid values to sweep
    fixed_params : override defaults for other parameters

    Returns
    -------
    DataFrame with columns: param_x, param_y, sharpe, bench_sharpe, excess_sharpe
    """
    defaults = {
        "risk_aversion": DEFAULT_RISK_AVERSION,
        "tilt_strength": DEFAULT_TILT_STRENGTH,
        "max_weight": DEFAULT_MAX_WEIGHT,
        "lookback": DEFAULT_LOOKBACK,
    }
    if fixed_params:
        defaults.update(fixed_params)

    records = []
    total = len(values_x) * len(values_y)
    for idx, (vx, vy) in enumerate(itertools.product(values_x, values_y)):
        params = dict(defaults)
        params[param_x] = vx
        params[param_y] = vy

        try:
            res = run_backtest(prices, scores, **params)
            sm = performance_metrics(res["strategy_returns"], "s")
            bm = performance_metrics(res["benchmark_returns"], "b")
            sharpe = sm["Sharpe Ratio"]
            bench_sharpe = bm["Sharpe Ratio"]
        except Exception:
            sharpe = np.nan
            bench_sharpe = np.nan

        records.append({
            param_x: vx,
            param_y: vy,
            "sharpe": sharpe,
            "bench_sharpe": bench_sharpe,
            "excess_sharpe": sharpe - bench_sharpe if not np.isnan(sharpe) else np.nan,
        })

        if (idx + 1) % 5 == 0 or idx + 1 == total:
            print(f"  [{idx + 1}/{total}]")

    return pd.DataFrame(records)


# ═══════════════════════════════════════════════════════════════════════════
#  Heatmap plotting
# ═══════════════════════════════════════════════════════════════════════════

def plot_sensitivity_heatmap(
    sweep_df: pd.DataFrame,
    param_x: str,
    param_y: str,
    metric: str = "sharpe",
    title: Optional[str] = None,
    save_path=None,
) -> plt.Figure:
    """Plot a single annotated heatmap from sweep results."""
    pivot = sweep_df.pivot(index=param_y, columns=param_x, values=metric)
    pivot = pivot.sort_index(ascending=False)

    fig, ax = plt.subplots(figsize=(max(7, len(pivot.columns) * 1.1),
                                    max(5, len(pivot) * 0.8)))
    sns.heatmap(pivot, annot=True, fmt=".2f", cmap="YlGnBu",
                linewidths=0.5, ax=ax,
                cbar_kws={"label": metric.replace("_", " ").title()})

    ax.set_xlabel(PARAM_LABELS.get(param_x, param_x))
    ax.set_ylabel(PARAM_LABELS.get(param_y, param_y))
    ax.set_title(title or f"Sensitivity: {metric.replace('_', ' ').title()}", fontsize=13)
    fig.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"Saved -> {save_path}")
    plt.close(fig)
    return fig


def run_all_sensitivity(
    prices: pd.DataFrame,
    scores: pd.DataFrame,
    save_dir=None,
) -> Dict[str, pd.DataFrame]:
    """Run pre-defined 2-D sweeps and save heatmaps.

    Sweeps:
      1. risk_aversion × tilt_strength
      2. max_weight × lookback
    """
    save_dir = save_dir or REPORTS_DIR
    results = {}

    # Sweep 1: risk_aversion × tilt_strength
    print("\nSweep 1/2: risk_aversion × tilt_strength")
    df1 = run_sensitivity_sweep(
        prices, scores,
        "risk_aversion", DEFAULT_GRIDS["risk_aversion"],
        "tilt_strength", DEFAULT_GRIDS["tilt_strength"],
    )
    results["ra_ts"] = df1
    plot_sensitivity_heatmap(
        df1, "risk_aversion", "tilt_strength", "sharpe",
        title="Sharpe Ratio: Risk Aversion × Tilt Strength",
        save_path=save_dir / "sensitivity_sharpe_ra_ts.png",
    )
    plot_sensitivity_heatmap(
        df1, "risk_aversion", "tilt_strength", "excess_sharpe",
        title="Excess Sharpe: Risk Aversion × Tilt Strength",
        save_path=save_dir / "sensitivity_excess_ra_ts.png",
    )

    # Sweep 2: max_weight × lookback
    print("\nSweep 2/2: max_weight × lookback")
    df2 = run_sensitivity_sweep(
        prices, scores,
        "max_weight", DEFAULT_GRIDS["max_weight"],
        "lookback", DEFAULT_GRIDS["lookback"],
    )
    results["mw_lb"] = df2
    plot_sensitivity_heatmap(
        df2, "max_weight", "lookback", "sharpe",
        title="Sharpe Ratio: Max Weight × Lookback",
        save_path=save_dir / "sensitivity_sharpe_mw_lb.png",
    )
    plot_sensitivity_heatmap(
        df2, "max_weight", "lookback", "excess_sharpe",
        title="Excess Sharpe: Max Weight × Lookback",
        save_path=save_dir / "sensitivity_excess_mw_lb.png",
    )

    return results


# ── CLI ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).parent))

    from asset_fetch import load_prices
    from macro_fetch import get_macro_panel
    from signal_generation import compute_composite_scores

    print("Loading data ...")
    prices = load_prices()
    macro = get_macro_panel(prices.index)

    print("Computing signals ...")
    scores = compute_composite_scores(prices, macro)

    print("Running sensitivity analysis (this may take a few minutes) ...")
    results = run_all_sensitivity(prices, scores)

    for key, df in results.items():
        path = DATA_DIR / f"sensitivity_{key}.csv"
        df.to_csv(path, index=False)
        print(f"Saved -> {path}")

    print("\nSensitivity analysis complete! Check reports/ folder.")
