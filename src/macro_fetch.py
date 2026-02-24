"""
EVDS Macro Data Fetcher
=======================
Fetches macro indicators from TCMB EVDS for regime scoring:
  - USD/TRY exchange rate  (daily)
  - CPI index → YoY %     (monthly)
  - TCMB WACF interest rate (weekly, proxy for policy rate)
"""

from evds import evdsAPI
import pandas as pd
from pathlib import Path

# ── Config ──────────────────────────────────────────────────────────────────
EVDS_API_KEY = "wKboFlV7Rc"

SERIES = {
    "USDTRY":       "TP.DK.USD.A.YTL",    # USD/TRY buying rate (daily)
    "CPI_INDEX":    "TP.FG.J0",            # CPI index 2003=100 (monthly)
    "WACF_RATE":    "TP.TRY.MT01",         # Weighted avg cost of funding (weekly)
}

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)


def _evds_client() -> evdsAPI:
    return evdsAPI(EVDS_API_KEY)


def _fetch_chunked(series_code: str, col_name: str, start: str, end: str) -> pd.DataFrame:
    """Fetch a daily EVDS series in yearly chunks to avoid the 1000-row limit."""
    evds = _evds_client()
    start_dt = pd.to_datetime(start, dayfirst=True)
    end_dt = pd.to_datetime(end, dayfirst=True)

    chunks = []
    current = start_dt
    while current < end_dt:
        chunk_end = min(current + pd.DateOffset(years=1) - pd.DateOffset(days=1), end_dt)
        s = current.strftime("%d-%m-%Y")
        e = chunk_end.strftime("%d-%m-%Y")
        df = evds.get_data([series_code], startdate=s, enddate=e)
        chunks.append(df)
        current = chunk_end + pd.DateOffset(days=1)

    result = pd.concat(chunks, ignore_index=True)
    return result


def fetch_usdtry(start: str = "01-01-2016", end: str = "24-02-2026") -> pd.Series:
    """Fetch daily USD/TRY exchange rate from EVDS."""
    df = _fetch_chunked(SERIES["USDTRY"], "TP_DK_USD_A_YTL", start, end)
    df["Date"] = pd.to_datetime(df["Tarih"], dayfirst=True)
    s = df.set_index("Date")["TP_DK_USD_A_YTL"].astype(float)
    s.name = "USDTRY"
    s = s.dropna().sort_index()
    # Remove duplicate dates (chunk overlap)
    s = s[~s.index.duplicated(keep="first")]
    return s


def fetch_cpi(start: str = "01-01-2015", end: str = "24-02-2026") -> pd.DataFrame:
    """Fetch monthly CPI index and compute YoY % change.

    Starts 1 year earlier so that the first YoY value aligns with the
    desired analysis start date.
    """
    evds = _evds_client()
    df = evds.get_data([SERIES["CPI_INDEX"]], startdate=start, enddate=end)

    # Parse "2024-1" style dates
    df["Date"] = pd.to_datetime(df["Tarih"], format="%Y-%m")
    df = df.set_index("Date").sort_index()
    df["CPI_INDEX"] = df["TP_FG_J0"].astype(float)
    df["CPI_YOY"] = df["CPI_INDEX"].pct_change(periods=12) * 100  # YoY %

    return df[["CPI_INDEX", "CPI_YOY"]].dropna()


def fetch_interest_rate(start: str = "01-01-2016", end: str = "24-02-2026") -> pd.Series:
    """Fetch weekly TCMB weighted average cost of funding (WACF)."""
    evds = _evds_client()
    df = evds.get_data([SERIES["WACF_RATE"]], startdate=start, enddate=end)
    # Tarih column is "dd-mm-yyyy" (the Friday of each week)
    df["Date"] = pd.to_datetime(df["Tarih"], dayfirst=True)
    s = df.set_index("Date")["TP_TRY_MT01"].astype(float)
    s.name = "WACF_RATE"
    s = s.dropna().sort_index()
    return s


def build_macro_panel(start: str = "01-01-2016", end: str = "24-02-2026") -> pd.DataFrame:
    """Build a unified daily-frequency macro panel.

    Monthly/weekly series are forward-filled to daily frequency so they
    can be aligned with daily stock prices.
    """
    print("Fetching USD/TRY ...")
    usdtry = fetch_usdtry(start, end)

    print("Fetching CPI ...")
    cpi = fetch_cpi(start="01-01-2015", end=end)

    print("Fetching WACF rate ...")
    rate = fetch_interest_rate(start, end)

    # Create daily date range from USDTRY trading days
    daily_idx = usdtry.index

    panel = pd.DataFrame(index=daily_idx)
    panel["USDTRY"] = usdtry
    panel["CPI_YOY"] = cpi["CPI_YOY"].reindex(daily_idx, method="ffill")
    panel["CPI_INDEX"] = cpi["CPI_INDEX"].reindex(daily_idx, method="ffill")
    panel["WACF_RATE"] = rate.reindex(daily_idx, method="ffill")

    # Derived: USD/TRY monthly % change (rolling 21-day)
    panel["USDTRY_CHG_1M"] = panel["USDTRY"].pct_change(periods=21) * 100

    panel = panel.dropna()
    print(f"Macro panel: {panel.shape[0]} rows, {panel.columns.tolist()}")
    return panel


def save_macro(panel: pd.DataFrame, filename: str = "macro_data.csv") -> Path:
    path = DATA_DIR / filename
    panel.to_csv(path)
    print(f"Saved -> {path}")
    return path


def load_macro(filename: str = "macro_data.csv") -> pd.DataFrame:
    path = DATA_DIR / filename
    return pd.read_csv(path, index_col=0, parse_dates=True)


# ── CLI ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    panel = build_macro_panel()
    save_macro(panel)

    print("\n── Macro Summary ──")
    print(panel.describe().round(2).to_string())
