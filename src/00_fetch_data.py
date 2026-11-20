"""Step 0: download daily adjusted close prices for the Nifty 200 stocks.

Minimal first version: plain yfinance request, one batch call, local cache.
The yfinance timezone/cookie cache is redirected inside this project folder.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import yfinance as yf

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import config  # noqa: E402
from utils import ensure_dirs, log  # noqa: E402


def main() -> None:
    ensure_dirs()

    # yfinance stores timezone + cookie data here instead of ~/.cache/py-yfinance.
    config.TZ_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    yf.set_tz_cache_location(str(config.TZ_CACHE_DIR))

    constituents = pd.read_csv(config.CONSTITUENTS_CSV)
    tickers = [f"{symbol}.NS" for symbol in constituents["Symbol"].astype(str)]
    log(f"Requesting {len(tickers)} tickers, period={config.PERIOD}, interval={config.INTERVAL}")

    data = yf.download(
        tickers,
        period=config.PERIOD,
        interval=config.INTERVAL,
        auto_adjust=True,          # 'Close' is the adjusted close
        progress=False,
        threads=True,
        group_by="column",
    )

    if data is None or data.empty:
        raise RuntimeError("yfinance returned no data; check network access / rate limits.")

    close = data["Close"] if isinstance(data.columns, pd.MultiIndex) else data
    close = close.dropna(axis=1, how="all")

    missing = sorted(set(tickers) - set(close.columns))
    log(f"Received {close.shape[1]} / {len(tickers)} tickers; missing: {missing}")

    close.index.name = "Date"
    close.to_csv(config.PRICES_RAW_CSV)
    log(f"Saved {config.PRICES_RAW_CSV.name}: {close.shape[0]} dates x {close.shape[1]} stocks")
    log(f"Date range: {close.index.min().date()} to {close.index.max().date()}")


if __name__ == "__main__":
    main()
