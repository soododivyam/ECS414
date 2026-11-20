"""Small shared helpers shared by the pipeline scripts."""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import config  # noqa: E402


def ensure_dirs() -> None:
    for path in (
        config.DERIVED_DIR,
        config.RESULTS_DIR,
        config.FIGURES_DIR,
        config.TABLES_DIR,
        config.TZ_CACHE_DIR,
    ):
        path.mkdir(parents=True, exist_ok=True)


def setup_plotting() -> None:
    plt.style.use("seaborn-v0_8-whitegrid")
    plt.rcParams.update({
        "figure.dpi": config.FIGURE_DPI,
        "savefig.dpi": config.FIGURE_DPI,
        "font.size": 10,
        "axes.titlesize": 12,
        "axes.labelsize": 11,
        "figure.autolayout": False,
    })


def save_figure(fig: plt.Figure, name: str, dpi: int | None = None) -> Path:
    """Save a figure into report/figures/ with a tight bounding box."""
    ensure_dirs()
    path = config.FIGURES_DIR / name
    fig.savefig(path, bbox_inches="tight", dpi=dpi or config.FIGURE_DPI)
    plt.close(fig)
    return path


def off_diagonal(matrix: np.ndarray) -> np.ndarray:
    """Return the strict upper triangle of a symmetric matrix."""
    return matrix[np.triu_indices_from(matrix, k=1)]


def log(message: str) -> None:
    print(f"[pipeline] {message}", flush=True)
