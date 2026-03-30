"""
BIST 100 (XU100) Benchmark Fetching via investpy
=================================================
Fetch XU100 using web scraping from Investing.com
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
import investpy

from config import DATA_DIR, DEFAULT_PRICE_START, DEFAULT_PRICE_END


def fetch_xu100_investpy(
    start: str = DEFAULT_PRICE_START,
    end: str = DEFAULT_PRICE_END,
) -> pd.Series:
    """
    Fetch BIST 100 (XU100) closing prices using investpy (web scraping).
    
    Parameters
    ----------
    start : str
        Start date (YYYY-MM-DD)
    end : str
        End date (YYYY-MM-DD)
    
    Returns
    -------
    pd.Series
        Daily closing prices indexed by date
    """
    print(f"Fetching BIST 100 (XU100) from Investing.com...")
    print(f"  Date range: {start} to {end}")
    
    try:
        # Parse dates
        start_dt = pd.to_datetime(start)
        end_dt = pd.to_datetime(end)
        
        print(f"  Using investpy library...", end=" ")
        
        # Fetch BIST 100 index
        # investpy uses format: DD/MM/YYYY
        df = investpy.indices.get_index_historical_data(
            index="BIST 100",
            country="Turkey",
            from_date=start_dt.strftime("%d/%m/%Y"),
            to_date=end_dt.strftime("%d/%m/%Y"),
        )
        
        if df is None or df.empty:
            raise ValueError("No data returned from investpy")
        
        print(f"✓ Downloaded {len(df)} rows")
        
        # Extract closing prices
        if "Close" in df.columns:
            prices = df["Close"]
        else:
            # Try to find price column
            price_cols = [c for c in df.columns if c.lower() in ['close', 'price', 'fiyat']]
            if price_cols:
                prices = df[price_cols[0]]
            else:
                prices = df.iloc[:, 0]  # Take first numeric column
        
        prices = pd.to_numeric(prices, errors='coerce').dropna()
        prices = prices[~prices.index.duplicated(keep='last')].sort_index()
        
        print(f"✓ Cleaned {len(prices)} rows for BIST 100")
        print(f"  Date range: {prices.index[0].date()} to {prices.index[-1].date()}")
        print(f"  Price range: {prices.min():.2f} to {prices.max():.2f}")
        
        return prices
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        raise


def calculate_returns(prices: pd.Series) -> pd.Series:
    """Calculate daily returns from price series."""
    return prices.pct_change(fill_method=None).dropna()


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    
    # Fetch XU100
    try:
        xu100_prices = fetch_xu100_investpy()
        
        # Save to CSV
        output_file = DATA_DIR / "bist100_prices.csv"
        xu100_prices.to_csv(output_file, header=["Close"])
        print(f"\n✓ Saved BIST 100 to {output_file}")
        
        # Calculate and save returns
        xu100_returns = calculate_returns(xu100_prices)
        returns_file = DATA_DIR / "bist100_returns.csv"
        xu100_returns.to_csv(returns_file, header=["Returns"])
        print(f"✓ Saved BIST 100 returns to {returns_file}")
        
        print("\n" + "="*60)
        print("BIST 100 Summary Statistics")
        print("="*60)
        total_ret = (xu100_prices.iloc[-1] / xu100_prices.iloc[0] - 1) * 100
        annual_vol = xu100_returns.std() * (252 ** 0.5) * 100
        annual_ret = xu100_returns.mean() * 252 * 100
        sharpe = (xu100_returns.mean() * 252) / (xu100_returns.std() * (252 ** 0.5))
        
        print(f"Total Return: {total_ret:.2f}%")
        print(f"Annual Volatility: {annual_vol:.2f}%")
        print(f"Annual Return: {annual_ret:.2f}%")
        print(f"Sharpe Ratio: {sharpe:.4f}")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ Failed to fetch XU100: {e}")
        sys.exit(1)
