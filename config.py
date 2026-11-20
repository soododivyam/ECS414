"""Shared configuration for the Nifty 200 correlation-network assignment.

All paths are resolved relative to this file, so every script can be run from
any working directory as long as the project folder structure is intact.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent

# Inputs
CONSTITUENTS_CSV = ROOT / "ind_nifty200list.csv"
PRICES_RAW_CSV = ROOT / "data" / "prices_raw.csv"

# Caches / derived data
TZ_CACHE_DIR = ROOT / "data" / "cache" / "yfinance"
DERIVED_DIR = ROOT / "data" / "derived"
PRICES_ALIGNED_CSV = DERIVED_DIR / "prices_aligned.csv"
RETURNS_CSV = DERIVED_DIR / "log_returns.csv"
CORRELATION_CSV = DERIVED_DIR / "correlation.csv"
GRAPH_PATH = DERIVED_DIR / "graph_primary.graphml"
DATA_QUALITY_PATH = DERIVED_DIR / "data_quality.txt"

# Outputs (kept inside report/ so that main.tex is self-contained on Overleaf)
FIGURES_DIR = ROOT / "report" / "figures"
TABLES_DIR = ROOT / "report" / "tables"
RESULTS_DIR = DERIVED_DIR / "results"

# Data / network parameters
PERIOD = "3y"
INTERVAL = "1d"
MIN_COVERAGE = 0.80           # keep a stock only if it has >= 80% of dates
MIN_CORR_PERIODS = None       # filled in preprocessing: 80% of trading days

# Primary network: highest threshold that keeps a connected giant component
THRESHOLD_GRID = [round(0.30 + 0.01 * i, 2) for i in range(46)]
MIN_AVG_DEGREE = 4.0
MIN_GIANT_FRACTION = 0.80
TARGET_DENSITY = 0.05         # fallback if no threshold satisfies the above

# Threshold sensitivity sweep (adapted to the observed correlation range)
SWEEP_THRESHOLDS = [0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70, 0.75]

# Reproducibility
RANDOM_SEED = 42
FIGURE_DPI = 160
