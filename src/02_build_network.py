"""Step 2: threshold the correlation matrix into a simple undirected network."""

from __future__ import annotations

import sys
from pathlib import Path

import networkx as nx
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import config  # noqa: E402
from utils import ensure_dirs, log  # noqa: E402
from network_utils import adjacency, graph_metrics  # noqa: E402


def choose_threshold(corr: np.ndarray) -> tuple[float, list[dict]]:
    """Pick the most stringent threshold that still leaves a connected giant component."""
    scan = [graph_metrics(nx.from_numpy_array(adjacency(corr, r))) for r in config.THRESHOLD_GRID]
    feasible = [
        (r, m) for r, m in zip(config.THRESHOLD_GRID, scan)
        if m["avg_degree"] >= config.MIN_AVG_DEGREE
        and m["giant_fraction"] >= config.MIN_GIANT_FRACTION
    ]
    if feasible:
        threshold = max(feasible, key=lambda x: x[0])[0]
        reason = "highest threshold with giant component >= 80% and avg degree >= 4"
    else:
        threshold = min(scan, key=lambda m: abs(m["density"] - config.TARGET_DENSITY))
        idx = scan.index(threshold)
        threshold = config.THRESHOLD_GRID[idx]
        reason = "fallback: density closest to 5%"
    log(f"Primary threshold r={threshold:.2f} ({reason})")
    return threshold, scan


def build_graph(corr: pd.DataFrame, threshold: float, constituents: pd.DataFrame) -> nx.Graph:
    tickers = list(corr.columns)
    values = corr.to_numpy()
    a = adjacency(values, threshold)

    graph = nx.Graph()
    graph.add_nodes_from(tickers)
    for i, u in enumerate(tickers):
        for j in range(i + 1, len(tickers)):
            if a[i, j]:
                graph.add_edge(u, tickers[j], correlation=float(values[i, j]))

    meta = constituents.set_index(constituents["Symbol"].astype(str) + ".NS")
    for ticker in tickers:
        row = meta.loc[ticker]
        graph.nodes[ticker]["company"] = str(row["Company Name"])
        graph.nodes[ticker]["sector"] = str(row["Industry"])
        graph.nodes[ticker]["symbol"] = ticker.removesuffix(".NS")
    return graph


def main() -> None:
    ensure_dirs()
    corr = pd.read_csv(config.CORRELATION_CSV, index_col=0)
    constituents = pd.read_csv(config.CONSTITUENTS_CSV)
    assert list(corr.index) == list(corr.columns), "correlation labels misaligned"

    threshold, scan = choose_threshold(corr.to_numpy())
    graph = build_graph(corr, threshold, constituents)
    metrics = graph_metrics(graph)
    giant = max(nx.connected_components(graph), key=len)
    giant_graph = graph.subgraph(giant)
    metrics["avg_path_length_giant"] = nx.average_shortest_path_length(giant_graph)
    metrics["diameter_giant"] = nx.diameter(giant_graph)
    expected_edges = int(adjacency(corr.to_numpy(), threshold).sum() // 2)
    assert graph.number_of_edges() == expected_edges, "edge count does not match adjacency"
    assert not any(graph.has_edge(u, u) for u in graph.nodes), "self-loop found"

    nx.write_graphml(graph, config.GRAPH_PATH)

    rows = [{"threshold": r, **m} for r, m in zip(config.THRESHOLD_GRID, scan)]
    pd.DataFrame(rows).to_csv(config.RESULTS_DIR / "threshold_scan.csv", index=False)
    pd.DataFrame([{"primary_threshold": threshold, **metrics}]).to_csv(
        config.RESULTS_DIR / "primary_network.csv", index=False
    )
    log(f"Primary network: {metrics}")
    log(f"Saved {config.GRAPH_PATH.name}")


if __name__ == "__main__":
    main()
