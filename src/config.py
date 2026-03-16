from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
REPORTS_DIR = PROJECT_ROOT / "reports"

DATA_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)


SECTORS = {
    "Mining/Industrial": ["EREGL.IS", "SISE.IS"],
    "Export-Oriented": ["TOASO.IS", "FROTO.IS", "THYAO.IS"],
    "Interest-Sensitive": ["GARAN.IS", "AKBNK.IS", "EKGYO.IS"],
    "Defensive/Retail": ["BIMAS.IS", "MGROS.IS"],
}

ALL_TICKERS = [ticker for tickers in SECTORS.values() for ticker in tickers]


PRICE_FILENAME = "bist_prices.csv"
MACRO_FILENAME = "macro_data.csv"
SCORES_FILENAME = "composite_scores.csv"
METRICS_FILENAME = "backtest_metrics.csv"
WEIGHTS_FILENAME = "weights_history.csv"


DEFAULT_PRICE_START = "2016-01-01"
DEFAULT_PRICE_END = "2026-02-24"
DEFAULT_BACKTEST_START = "2017-06-01"


DEFAULT_LOOKBACK = 252
DEFAULT_RISK_AVERSION = 5.0
DEFAULT_TILT_STRENGTH = 0.5
DEFAULT_MAX_WEIGHT = 0.25
DEFAULT_MIN_WEIGHT = 0.0
DEFAULT_SHRINK_FACTOR = 0.30


DEFAULT_TECH_WEIGHT = 0.60
DEFAULT_MACRO_WEIGHT = 0.40


USDTRY_RELEASE_LAG_DAYS = 1
WACF_RELEASE_LAG_DAYS = 1
CPI_RELEASE_LAG_MONTHS = 1
USDTRY_CHANGE_LOOKBACK_DAYS = 21


TECHNICAL_WINDOWS = {
    "ma_short": 50,
    "ma_long": 200,
    "momentum": 63,
    "volatility": 63,
    "volatility_baseline": 252,
}


EVDS_API_KEY_ENV = "wKboFlV7Rc"
