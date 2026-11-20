"""Step 4: turn result CSVs into ready-to-include LaTeX (booktabs) tables."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import config  # noqa: E402
from utils import ensure_dirs, log  # noqa: E402

RESULTS = config.RESULTS_DIR
TABLES = config.TABLES_DIR


def write_table(df: pd.DataFrame, filename: str, caption: str, label: str,
                float_fmt: str | None = "%.3f", escape: bool = True) -> None:
    text = df.to_latex(
        index=False,
        escape=escape,
        float_format=float_fmt,
        caption=caption,
        label=label,
        column_format="l" + "l" * (df.shape[1] - 1),
    )
    # [!ht]: try the exact source position first (! relaxes LaTeX's float
    # limits), otherwise the top of a page -- stricter than [htbp], but not
    # as rigid as the float package's [H].
    text = text.replace("\\begin{table}", "\\begin{table}[!ht]\n\\centering")
    (TABLES / filename).write_text(text, encoding="utf-8")


def main() -> None:
    ensure_dirs()

    for name, title in (
        ("degree", "Top-10 stocks by degree centrality"),
        ("betweenness", "Top-10 stocks by betweenness centrality"),
        ("eigenvector", "Top-10 stocks by eigenvector centrality (giant component)"),
    ):
        df = pd.read_csv(RESULTS / f"top10_{name}.csv")
        df = df.drop(columns=["Ticker"])
        df = df.rename(columns={"Score": "Centrality"})
        write_table(df, f"top10_{name}.tex", title, f"tab:top10-{name}")

    degree_stats = pd.read_csv(RESULTS / "degree_stats.csv").iloc[0]
    degree_table = pd.DataFrame([
        {"Statistic": "Mean degree", "Value": f"{degree_stats['mean_degree']:.2f}"},
        {"Statistic": "Median degree", "Value": f"{degree_stats['median_degree']:.0f}"},
        {"Statistic": "Maximum degree", "Value": str(int(degree_stats["max_degree"]))},
        {"Statistic": "Standard deviation", "Value": f"{degree_stats['std_degree']:.2f}"},
        {"Statistic": "Isolated nodes", "Value": str(int(degree_stats["isolates"]))},
        {"Statistic": "Log-log slope (all points)", "Value": f"{degree_stats['loglog_slope_all']:.2f}"},
        {"Statistic": "R-squared (all points)", "Value": f"{degree_stats['loglog_r2_all']:.2f}"},
        {"Statistic": "Log-log slope (tail)", "Value": f"{degree_stats['loglog_slope_tail']:.2f}"},
        {"Statistic": "R-squared (tail)", "Value": f"{degree_stats['loglog_r2_tail']:.2f}"},
    ])
    write_table(degree_table, "degree_stats.tex",
                "Summary of the degree distribution and log-log fits",
                "tab:degree", float_fmt=None)

    primary = pd.read_csv(RESULTS / "primary_network.csv").iloc[0]
    homophily = pd.read_csv(RESULTS / "homophily_summary.csv").iloc[0]
    degree = pd.read_csv(RESULTS / "degree_stats.csv").iloc[0]
    summary = pd.DataFrame([
        {"Metric": "Primary correlation threshold", "Value": f"{primary['primary_threshold']:.2f}"},
        {"Metric": "Nodes (stocks)", "Value": str(int(primary["nodes"]))},
        {"Metric": "Edges", "Value": str(int(primary["edges"]))},
        {"Metric": "Density", "Value": f"{primary['density']:.3f}"},
        {"Metric": "Average degree", "Value": f"{primary['avg_degree']:.2f}"},
        {"Metric": "Connected components", "Value": str(int(primary["components"]))},
        {"Metric": "Giant component size", "Value": str(int(primary["giant_size"]))},
        {"Metric": "Giant component fraction", "Value": f"{primary['giant_fraction']:.3f}"},
        {"Metric": "Average path length (giant)", "Value": f"{primary['avg_path_length_giant']:.3f}"},
        {"Metric": "Diameter (giant)", "Value": str(int(primary["diameter_giant"]))},
        {"Metric": "Isolated nodes", "Value": str(int(primary["isolates"]))},
        {"Metric": "Average clustering coefficient", "Value": f"{homophily['average_clustering']:.3f}"},
        {"Metric": "Same-sector edge fraction", "Value": f"{homophily['observed_same_sector_fraction']:.3f}"},
        {"Metric": "Degree log-log tail slope", "Value": f"{degree['loglog_slope_tail']:.2f}"},
    ])
    write_table(summary, "network_summary.tex",
                "Summary statistics of the primary correlation network",
                "tab:network-summary", float_fmt=None)

    sweep = pd.read_csv(RESULTS / "threshold_sensitivity.csv")
    sweep = sweep.rename(columns={
        "threshold": "$r$", "edges": "Edges", "avg_path_length_giant": "Path length",
        "giant_fraction": "Giant fraction", "isolates": "Isolates",
    })
    sweep = sweep[["$r$", "Edges", "Path length", "Giant fraction", "Isolates"]]
    write_table(sweep, "threshold_sensitivity.tex",
                "Sensitivity of network metrics to the correlation threshold",
                "tab:sensitivity", escape=False)

    corr = pd.read_csv(RESULTS / "centrality_correlations.csv", index_col=0)
    corr.index.name = "Measure"
    corr = corr.reset_index()
    write_table(corr, "centrality_correlations.tex",
                "Spearman rank correlations between centrality measures",
                "tab:centrality-corr")

    sectors = pd.read_csv(RESULTS / "clustering_by_sector.csv")
    sectors = sectors.rename(columns={"MeanClustering": "Mean clustering"})
    write_table(sectors, "clustering_by_sector.tex",
                "Mean local clustering coefficient by sector, highest to lowest",
                "tab:clustering-sector")

    log(f"Wrote {len(list(TABLES.glob('*.tex')))} LaTeX tables to {TABLES}")


if __name__ == "__main__":
    main()
