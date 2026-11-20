"""Core network-construction helpers shared by steps 2 and 3."""

from __future__ import annotations

import networkx as nx
import numpy as np


def adjacency(corr: np.ndarray, threshold: float) -> np.ndarray:
    """Unweighted adjacency: 1 where correlation >= threshold, zero diagonal."""
    a = (corr >= threshold).astype(np.int8)
    np.fill_diagonal(a, 0)
    return a


def graph_metrics(graph: nx.Graph) -> dict:
    components = sorted((len(c) for c in nx.connected_components(graph)), reverse=True)
    n = graph.number_of_nodes()
    return {
        "nodes": n,
        "edges": graph.number_of_edges(),
        "density": nx.density(graph),
        "avg_degree": 2 * graph.number_of_edges() / n if n else 0.0,
        "components": len(components),
        "giant_size": components[0] if components else 0,
        "giant_fraction": components[0] / n if n else 0.0,
        "isolates": nx.number_of_isolates(graph),
    }
