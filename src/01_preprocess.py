"""Step 1: clean prices, compute log returns and the Pearson correlation matrix."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import config  # noqa: E402
from utils import ensure_dirs, log, off_diagonal  # noqa: E402


def load_inputs() -> tuple[pd.DataFrame, pd.DataFrame]:
    constituents = pd.read_csv(config.CONSTITUENTS_CSV)
    prices = pd.read_csv(config.PRICES_RAW_CSV, index_col=0, parse_dates=True)
    prices = prices.sort_index()
    prices.index.name = "Date"
    return constituents, prices


def clean_prices(prices: pd.DataFrame) -> tuple[pd.DataFrame, list[tuple[str, float]]]:
    coverage = prices.notna().mean()
    dropped = sorted(
        [(ticker, float(coverage[ticker])) for ticker in prices.columns
         if coverage[ticker] < config.MIN_COVERAGE],
        key=lambda x: x[1],
    )
    kept = prices.drop(columns=[t for t, _ in dropped])
    rows_before = len(kept)
    kept = kept.dropna(axis=0, how="any")
    log(f"Dropped {len(dropped)} short-history tickers; removed "
        f"{rows_before - len(kept)} dates with isolated missing values")
    return kept, dropped


def main() -> None:
    ensure_dirs()
    constituents, raw = load_inputs()
    log(f"Raw prices: {raw.shape[0]} dates x {raw.shape[1]} tickers")

    prices, dropped = clean_prices(raw)
    returns = np.log(prices).diff().dropna(how="any")

    min_periods = int(config.MIN_COVERAGE * len(returns))
    corr = returns.corr(method="pearson", min_periods=min_periods)
    vals = off_diagonal(corr.to_numpy())
    log(f"Final sample: {prices.shape[0]} dates x {prices.shape[1]} stocks; "
        f"{returns.shape[0]} return observations")
    log(f"Correlation range: {np.nanmin(vals):.3f} to {np.nanmax(vals):.3f}; "
        f"median {np.nanmedian(vals):.3f}")

    # Sanity checks
    assert np.allclose(corr.to_numpy(), corr.to_numpy().T, equal_nan=True), "correlation not symmetric"
    assert np.allclose(np.diag(corr.to_numpy()), 1.0), "correlation diagonal != 1"
    assert corr.notna().all().all(), "NaN correlations remain"

    prices.to_csv(config.PRICES_ALIGNED_CSV)
    returns.to_csv(config.RETURNS_CSV)
    corr.to_csv(config.CORRELATION_CSV)

    lines = [
        "DATA QUALITY SUMMARY",
        "====================",
        f"Downloaded tickers: {raw.shape[1]}",
        f"Download window: {raw.index.min().date()} to {raw.index.max().date()}",
        f"Minimum required price coverage: {config.MIN_COVERAGE:.0%}",
        f"Dropped tickers ({len(dropped)}): "
        + ", ".join(f"{t} ({c:.1%})" for t, c in dropped),
        f"Dates removed for isolated missing values: {raw.shape[0] - prices.shape[0]}",
        f"Final stocks: {prices.shape[1]}",
        f"Final trading dates: {prices.shape[0]} ({prices.index.min().date()} to {prices.index.max().date()})",
        f"Log-return observations: {returns.shape[0]}",
        f"Correlation min/median/max: {np.nanmin(vals):.3f} / {np.nanmedian(vals):.3f} / {np.nanmax(vals):.3f}",
        "",
        "Sector counts (NSE Industry):",
    ]
    counts = (constituents.set_index(constituents["Symbol"].astype(str) + ".NS")
              .loc[prices.columns, "Industry"].value_counts())
    lines += [f"  {sector}: {n}" for sector, n in counts.items()]
    config.DATA_QUALITY_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    log(f"Saved derived data and {config.DATA_QUALITY_PATH.name}")


if __name__ == "__main__":
    main()
