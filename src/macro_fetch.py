"""
EVDS Macro Data Fetcher
=======================
Builds a lag-safe macro panel aligned to BIST trading dates.
"""

import json
import os
from pathlib import Path

import pandas as pd
from evds import evdsAPI

from config import (
    CPI_RELEASE_LAG_MONTHS,
    DATA_DIR,
    DEFAULT_PRICE_END,
    DEFAULT_PRICE_START,
    EVDS_API_KEY_ENV,
    MACRO_FILENAME,
    USDTRY_CHANGE_LOOKBACK_DAYS,
)


SERIES = {
    "USDTRY": "TP.DK.USD.A.YTL",
    "CPI_INDEX": "TP.FG.J0",
    "WACF_RATE": "TP.TRY.MT01",
}

SAFE_MACRO_PANEL_VERSION = 1


def _metadata_path(filename: str = MACRO_FILENAME) -> Path:
    return (DATA_DIR / filename).with_suffix(".meta.json")


def _evds_client(api_key: str | None = None) -> evdsAPI:
    configured_value = api_key or EVDS_API_KEY_ENV
    token = os.getenv(configured_value, configured_value)
    if not token:
        raise ValueError(
            "EVDS API key not found in config or environment."
        )
    return evdsAPI(token)


def _fetch_chunked(series_code: str, start: str, end: str) -> pd.DataFrame:
    """Fetch a daily EVDS series in yearly chunks to avoid row limits."""
    evds = _evds_client()
    start_dt = pd.to_datetime(start, dayfirst=True)
    end_dt = pd.to_datetime(end, dayfirst=True)

    chunks = []
    current = start_dt
    while current < end_dt:
        chunk_end = min(current + pd.DateOffset(years=1) - pd.DateOffset(days=1), end_dt)
        df = evds.get_data(
            [series_code],
            startdate=current.strftime("%d-%m-%Y"),
            enddate=chunk_end.strftime("%d-%m-%Y"),
        )
        chunks.append(df)
        current = chunk_end + pd.DateOffset(days=1)

    return pd.concat(chunks, ignore_index=True)


def _format_evds_date(value: str) -> str:
    return pd.to_datetime(value).strftime("%d-%m-%Y")


def _aligned_series_from_availability(
    series: pd.Series,
    trading_index: pd.DatetimeIndex,
    availability_dates: pd.DatetimeIndex,
) -> pd.Series:
    observed = series.dropna().sort_index()
    if observed.empty:
        return pd.Series(index=trading_index, dtype=float, name=series.name)

    positions = trading_index.searchsorted(availability_dates, side="left")
    valid = positions < len(trading_index)
    if not valid.any():
        return pd.Series(index=trading_index, dtype=float, name=series.name)

    aligned = pd.Series(
        observed.iloc[valid].to_numpy(),
        index=trading_index.take(positions[valid]),
        name=series.name,
    )
    aligned = aligned.groupby(level=0).last()
    return aligned.reindex(trading_index, method="ffill")


def _aligned_frame_from_availability(
    frame: pd.DataFrame,
    trading_index: pd.DatetimeIndex,
    availability_dates: pd.DatetimeIndex,
) -> pd.DataFrame:
    observed = frame.dropna(how="any").sort_index()
    if observed.empty:
        return pd.DataFrame(index=trading_index, columns=frame.columns, dtype=float)

    positions = trading_index.searchsorted(availability_dates, side="left")
    valid = positions < len(trading_index)
    if not valid.any():
        return pd.DataFrame(index=trading_index, columns=frame.columns, dtype=float)

    aligned = observed.iloc[valid].copy()
    aligned.index = trading_index.take(positions[valid])
    aligned = aligned.groupby(level=0).last()
    return aligned.reindex(trading_index, method="ffill")


def fetch_usdtry(
    start: str = DEFAULT_PRICE_START,
    end: str = DEFAULT_PRICE_END,
) -> pd.Series:
    """Fetch daily USD/TRY exchange rate from EVDS."""
    df = _fetch_chunked(SERIES["USDTRY"], start=start, end=end)
    df["Date"] = pd.to_datetime(df["Tarih"], dayfirst=True)
    series = df.set_index("Date")["TP_DK_USD_A_YTL"].astype(float)
    series.name = "USDTRY"
    return series.dropna().sort_index()[lambda s: ~s.index.duplicated(keep="last")]


def fetch_cpi(
    start: str = "01-01-2015",
    end: str = DEFAULT_PRICE_END,
) -> pd.DataFrame:
    """Fetch monthly CPI index and compute YoY inflation."""
    evds = _evds_client()
    df = evds.get_data(
        [SERIES["CPI_INDEX"]],
        startdate=_format_evds_date(start),
        enddate=_format_evds_date(end),
    )
    df["Date"] = pd.to_datetime(df["Tarih"], format="%Y-%m")
    df = df.set_index("Date").sort_index()
    df["CPI_INDEX"] = df["TP_FG_J0"].astype(float)
    df["CPI_YOY"] = df["CPI_INDEX"].pct_change(periods=12) * 100
    return df[["CPI_INDEX", "CPI_YOY"]].dropna()


def fetch_interest_rate(
    start: str = DEFAULT_PRICE_START,
    end: str = DEFAULT_PRICE_END,
) -> pd.Series:
    """Fetch weekly TCMB weighted average cost of funding."""
    evds = _evds_client()
    df = evds.get_data(
        [SERIES["WACF_RATE"]],
        startdate=_format_evds_date(start),
        enddate=_format_evds_date(end),
    )
    df["Date"] = pd.to_datetime(df["Tarih"], dayfirst=True)
    series = df.set_index("Date")["TP_TRY_MT01"].astype(float)
    series.name = "WACF_RATE"
    return series.dropna().sort_index()


def build_macro_panel(
    trading_index: pd.DatetimeIndex,
    start: str = DEFAULT_PRICE_START,
    end: str = DEFAULT_PRICE_END,
) -> pd.DataFrame:
    """Build a lag-safe daily macro panel aligned to the trading calendar."""
    trading_index = pd.DatetimeIndex(trading_index).sort_values().unique()

    print("Fetching USD/TRY ...")
    usdtry = fetch_usdtry(start=start, end=end)

    print("Fetching CPI ...")
    cpi = fetch_cpi(end=end)

    print("Fetching WACF rate ...")
    rate = fetch_interest_rate(start=start, end=end)

    panel = pd.DataFrame(index=trading_index)
    panel["USDTRY"] = _aligned_series_from_availability(
        usdtry,
        trading_index,
        pd.DatetimeIndex(usdtry.index) + pd.Timedelta(days=1),
    )
    panel["WACF_RATE"] = _aligned_series_from_availability(
        rate,
        trading_index,
        pd.DatetimeIndex(rate.index) + pd.Timedelta(days=1),
    )

    cpi_availability = pd.DatetimeIndex(cpi.index) + pd.offsets.MonthBegin(CPI_RELEASE_LAG_MONTHS)
    cpi_aligned = _aligned_frame_from_availability(cpi, trading_index, cpi_availability)
    panel[["CPI_INDEX", "CPI_YOY"]] = cpi_aligned[["CPI_INDEX", "CPI_YOY"]]
    panel["USDTRY_CHG_1M"] = panel["USDTRY"].pct_change(periods=USDTRY_CHANGE_LOOKBACK_DAYS) * 100

    panel = panel.dropna().sort_index()
    print(f"Macro panel: {panel.shape[0]} rows, {panel.columns.tolist()}")
    return panel


def sanitize_cached_macro_panel(
    panel: pd.DataFrame,
    trading_index: pd.DatetimeIndex,
) -> pd.DataFrame:
    """Convert a legacy daily macro cache into the new lag-safe aligned format."""
    trading_index = pd.DatetimeIndex(trading_index).sort_values().unique()
    cached = panel.copy()
    cached.index = pd.to_datetime(cached.index)
    cached = cached.sort_index()

    safe_panel = pd.DataFrame(index=trading_index)
    safe_panel["USDTRY"] = cached["USDTRY"].reindex(trading_index).ffill().shift(1)
    safe_panel["WACF_RATE"] = cached["WACF_RATE"].reindex(trading_index).ffill().shift(1)

    monthly_cpi = cached[["CPI_INDEX", "CPI_YOY"]].groupby(cached.index.to_period("M")).last()
    monthly_cpi.index = monthly_cpi.index.to_timestamp(how="start") + pd.offsets.MonthBegin(
        CPI_RELEASE_LAG_MONTHS
    )
    safe_panel[["CPI_INDEX", "CPI_YOY"]] = monthly_cpi.reindex(trading_index, method="ffill")
    safe_panel["USDTRY_CHG_1M"] = (
        safe_panel["USDTRY"].pct_change(periods=USDTRY_CHANGE_LOOKBACK_DAYS) * 100
    )

    return safe_panel.dropna().sort_index()


def save_macro(panel: pd.DataFrame, filename: str = MACRO_FILENAME) -> Path:
    path = DATA_DIR / filename
    panel.to_csv(path)

    metadata = {
        "panel_version": SAFE_MACRO_PANEL_VERSION,
        "aligned_to_trading_calendar": True,
        "lag_policy": {
            "usdtry_release_lag_days": 1,
            "wacf_release_lag_days": 1,
            "cpi_release_lag_months": CPI_RELEASE_LAG_MONTHS,
        },
        "start_date": panel.index.min().strftime("%Y-%m-%d"),
        "end_date": panel.index.max().strftime("%Y-%m-%d"),
    }
    _metadata_path(filename).write_text(json.dumps(metadata, indent=2))
    print(f"Saved -> {path}")
    return path


def load_macro(filename: str = MACRO_FILENAME) -> pd.DataFrame:
    path = DATA_DIR / filename
    return pd.read_csv(path, index_col=0, parse_dates=True)


def macro_cache_is_safe(filename: str = MACRO_FILENAME) -> bool:
    meta_path = _metadata_path(filename)
    if not meta_path.exists():
        return False

    try:
        metadata = json.loads(meta_path.read_text())
    except json.JSONDecodeError:
        return False

    return metadata.get("panel_version") == SAFE_MACRO_PANEL_VERSION


def get_macro_panel(
    trading_index: pd.DatetimeIndex,
    filename: str = MACRO_FILENAME,
    refresh: bool = False,
) -> pd.DataFrame:
    """Return a lag-safe macro panel, refreshing from EVDS when possible."""
    path = DATA_DIR / filename
    safe_cache = path.exists() and macro_cache_is_safe(filename)

    if path.exists() and safe_cache and not refresh:
        return load_macro(filename)

    try:
        panel = build_macro_panel(trading_index=trading_index)
        save_macro(panel, filename=filename)
        return panel
    except Exception as exc:
        if not path.exists():
            raise

        cached = load_macro(filename)
        if safe_cache:
            print(f"Live macro refresh failed ({exc}). Using cached lag-safe macro panel.")
            return cached

        migrated = sanitize_cached_macro_panel(cached, trading_index=trading_index)
        save_macro(migrated, filename=filename)
        print(
            f"Live macro refresh failed ({exc}). Migrated cached macro panel to lag-safe format."
        )
        return migrated


if __name__ == "__main__":
    from asset_fetch import load_prices

    prices = load_prices()
    panel = get_macro_panel(prices.index, refresh=True)

    print("\n── Macro Summary ──")
    print(panel.describe().round(2).to_string())
