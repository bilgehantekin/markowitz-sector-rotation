import numpy as np
import pandas as pd

from asset_fetch import clean_prices
from backtest import get_rebalance_dates
from macro_fetch import sanitize_cached_macro_panel
from optimization import markowitz_optimize, validate_weight_vector


def test_clean_prices_removes_synthetic_non_trading_rows():
    index = pd.to_datetime(
        ["2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05"]
    )
    prices = pd.DataFrame(
        {
            "AAA.IS": [10.0, 11.0, 11.0, 12.0],
            "BBB.IS": [20.0, 19.0, 19.0, 18.0],
        },
        index=index,
    )

    cleaned = clean_prices(prices)

    assert pd.Timestamp("2024-01-04") not in cleaned.index
    assert len(cleaned) == 3


def test_sanitize_cached_macro_panel_applies_one_month_cpi_lag():
    trading_index = pd.date_range("2024-01-02", periods=65, freq="B")
    cached = pd.DataFrame(index=trading_index)
    cached["USDTRY"] = np.linspace(30.0, 36.4, len(trading_index))
    cached["WACF_RATE"] = 42.5

    cpi_map = {}
    for dt in trading_index:
        if dt.month == 1:
            cpi_map[dt] = (100.0, 10.0)
        elif dt.month == 2:
            cpi_map[dt] = (110.0, 20.0)
        else:
            cpi_map[dt] = (120.0, 30.0)

    cached["CPI_INDEX"] = [cpi_map[dt][0] for dt in trading_index]
    cached["CPI_YOY"] = [cpi_map[dt][1] for dt in trading_index]
    cached["USDTRY_CHG_1M"] = cached["USDTRY"].pct_change(periods=21) * 100

    safe_panel = sanitize_cached_macro_panel(cached, trading_index=trading_index)

    assert safe_panel.loc["2024-02-15", "CPI_YOY"] == 10.0
    assert safe_panel.loc["2024-03-15", "CPI_YOY"] == 20.0


def test_get_rebalance_dates_uses_last_trading_date_in_month():
    index = pd.to_datetime(
        [
            "2024-01-29",
            "2024-01-30",
            "2024-02-27",
            "2024-02-29",
            "2024-03-27",
        ]
    )

    rebalance_dates = get_rebalance_dates(index)

    assert rebalance_dates == [
        pd.Timestamp("2024-01-30"),
        pd.Timestamp("2024-02-29"),
        pd.Timestamp("2024-03-27"),
    ]


def test_markowitz_optimizer_respects_constraints():
    mu = np.array([0.18, 0.12, 0.10, 0.08, 0.06])
    sigma = np.diag([0.05, 0.04, 0.03, 0.02, 0.01])

    weights = markowitz_optimize(mu, sigma, risk_aversion=4.0, max_weight=0.25)
    validation = validate_weight_vector(weights, max_weight=0.25)

    assert validation["sum_to_one"]
    assert validation["non_negative"]
    assert validation["within_cap"]
