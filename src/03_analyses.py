"""Step 3: the four requested analyses (A-D) plus network visualisations."""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
import matplotlib as mpl
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import config  # noqa: E402
from utils import ensure_dirs, log, save_figure, setup_plotting  # noqa: E402
from network_utils import adjacency, graph_metrics  # noqa: E402


def load_graph() -> tuple[nx.Graph, pd.DataFrame]:
    graph = nx.read_graphml(config.GRAPH_PATH)
    corr = pd.read_csv(config.CORRELATION_CSV, index_col=0)
    return graph, corr


def primary_threshold() -> float:
    return float(pd.read_csv(config.RESULTS_DIR / "primary_network.csv")["primary_threshold"].iloc[0])


# --------------------------------------------------------------------------- A
def degree_analysis(graph: nx.Graph) -> None:
    log("A: degree distribution")
    degrees = np.array([d for _, d in graph.degree()])
    counts = np.bincount(degrees, minlength=degrees.max() + 1)
    k = np.arange(len(counts))

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(k, counts, color="#3b6fb6", width=0.8)
    ax.set(xlabel="Degree k", ylabel="Number of stocks",
           title="Degree distribution of the Nifty 200 correlation network (linear scale)")
    save_figure(fig, "degree_linear.png")

    positive = k[(counts > 0) & (k > 0)]
    freq = counts[(counts > 0) & (k > 0)]
    slope, intercept, r_value, _, _ = stats.linregress(np.log(positive), np.log(freq))
    tail = positive >= max(5, int(np.median(degrees)))
    tail_slope, tail_intercept, tail_r, _, _ = stats.linregress(
        np.log(positive[tail]), np.log(freq[tail])
    )

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.scatter(positive, freq, color="#3b6fb6", s=42, label="Observed")
    xs = np.logspace(np.log10(positive.min()), np.log10(positive.max()), 100)
    ax.plot(xs, np.exp(intercept) * xs ** slope, "r--",
            label=f"All-point fit: slope {slope:.2f}")
    xt = np.logspace(np.log10(positive[tail].min()), np.log10(positive[tail].max()), 100)
    ax.plot(xt, np.exp(tail_intercept) * xt ** tail_slope, "g-.",
            label=f"Tail fit (k >= {positive[tail].min()}): slope {tail_slope:.2f}")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set(xlabel="Degree k (log)", ylabel="Number of stocks (log)",
           title="Degree distribution on log-log scales")
    ax.legend()
    save_figure(fig, "degree_loglog.png")

    pd.DataFrame([{
        "mean_degree": degrees.mean(),
        "median_degree": float(np.median(degrees)),
        "max_degree": degrees.max(),
        "std_degree": degrees.std(ddof=1),
        "isolates": int((degrees == 0).sum()),
        "loglog_slope_all": slope,
        "loglog_r2_all": r_value ** 2,
        "loglog_slope_tail": tail_slope,
        "loglog_r2_tail": tail_r ** 2,
    }]).to_csv(config.RESULTS_DIR / "degree_stats.csv", index=False)


# --------------------------------------------------------------------------- B
def centrality_analysis(graph: nx.Graph) -> None:
    log("B: centralities")
    deg = nx.degree_centrality(graph)
    bet = nx.betweenness_centrality(graph, normalized=True, seed=config.RANDOM_SEED)
    # For a disconnected graph, eigenvector centrality is well-defined only on
    # the largest connected component; nodes outside it are assigned zero.
    giant = max(nx.connected_components(graph), key=len)
    eig_giant = nx.eigenvector_centrality_numpy(
        graph.subgraph(giant), max_iter=2000, tol=1e-10
    )
    eig = {node: eig_giant.get(node, 0.0) for node in graph.nodes()}

    frames = []
    for name, scores in (("degree", deg), ("betweenness", bet), ("eigenvector", eig)):
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:10]
        table = pd.DataFrame([
            {"Rank": i, "Ticker": ticker,
             "Company": graph.nodes[ticker]["company"],
             "Sector": graph.nodes[ticker]["sector"],
             "Score": float(score)}
            for i, (ticker, score) in enumerate(ranked, 1)
        ])
        table.to_csv(config.RESULTS_DIR / f"top10_{name}.csv", index=False)
        frames.append((name, table))

    all_scores = pd.DataFrame({
        "Ticker": list(graph.nodes()),
        "Company": [graph.nodes[n]["company"] for n in graph.nodes()],
        "Sector": [graph.nodes[n]["sector"] for n in graph.nodes()],
        "Degree": pd.Series(deg),
        "Betweenness": pd.Series(bet),
        "Eigenvector": pd.Series(eig),
    })
    all_scores.to_csv(config.RESULTS_DIR / "centrality_scores.csv", index=False)
    corr = all_scores[["Degree", "Betweenness", "Eigenvector"]].corr(method="spearman")
    corr.to_csv(config.RESULTS_DIR / "centrality_correlations.csv")

    fig, axes = plt.subplots(1, 3, figsize=(15, 6))
    for ax, (name, table) in zip(axes, frames):
        ax.barh(table["Ticker"][::-1], table["Score"][::-1], color="#3b6fb6")
        ax.set_title(f"Top 10: {name} centrality")
        ax.set_xlabel("Centrality score")
    fig.suptitle("Top-10 centrality leaderboards", fontsize=14)
    fig.tight_layout()
    save_figure(fig, "top10_centralities.png")


# --------------------------------------------------------------------------- C
def clustering_analysis(graph: nx.Graph, threshold: float) -> None:
    log("C: clustering and sector homophily")
    local = nx.clustering(graph)
    avg = nx.average_clustering(graph)
    random_avg = nx.average_clustering(nx.gnp_random_graph(
        graph.number_of_nodes(), nx.density(graph), seed=config.RANDOM_SEED))

    sector = {n: graph.nodes[n]["sector"] for n in graph.nodes()}
    sector_counts = pd.Series(list(sector.values())).value_counts()
    same = sum(1 for u, v in graph.edges() if sector[u] == sector[v])

    # Expected fraction for a random graph with the same sector sizes.
    n = graph.number_of_nodes()
    baseline = sum(s * (s - 1) for s in sector_counts) / (n * (n - 1))
    communities = [[node for node in graph.nodes() if graph.nodes[node]["sector"] == s]
                   for s in sector_counts.index]
    modularity = nx.community.modularity(graph, communities)

    rows = [{
        "primary_threshold": threshold,
        "average_clustering": avg,
        "random_graph_clustering": random_avg,
        "same_sector_edges": same,
        "total_edges": graph.number_of_edges(),
        "observed_same_sector_fraction": same / graph.number_of_edges(),
        "baseline_same_sector_fraction": baseline,
        "homophily_ratio": (same / graph.number_of_edges()) / baseline,
        "sector_modularity": modularity,
        "n_sectors": len(sector_counts),
    }]
    pd.DataFrame(rows).to_csv(config.RESULTS_DIR / "homophily_summary.csv", index=False)

    sector_table = (pd.DataFrame({"Sector": pd.Series(sector), "Clustering": pd.Series(local)})
                    .groupby("Sector", as_index=False)
                    .agg(Stocks=("Clustering", "size"), MeanClustering=("Clustering", "mean")))
    sector_table = sector_table.sort_values("MeanClustering", ascending=False)
    sector_table.to_csv(config.RESULTS_DIR / "clustering_by_sector.csv", index=False)

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.hist(list(local.values()), bins=20, color="#3b6fb6", edgecolor="white")
    ax.axvline(avg, color="red", linestyle="--", label=f"Mean = {avg:.3f}")
    ax.set(xlabel="Local clustering coefficient", ylabel="Number of stocks",
           title="Local clustering distribution")
    ax.legend()
    save_figure(fig, "clustering_distribution.png")

    log("Drawing sector-coloured network")
    colour_map = mpl.colormaps["tab20"]
    sector_list = list(sector_counts.index)
    colours = {s: colour_map(i / max(len(sector_list) - 1, 1))
               for i, s in enumerate(sector_list)}

    # --- Panel (a): sector-level chord diagram -------------------------------
    sector_graph = nx.Graph()
    for name, count in sector_counts.items():
        sector_graph.add_node(name, stocks=int(count))
    for u, v in graph.edges():
        su, sv = sector[u], sector[v]
        if su == sv:
            continue
        if sector_graph.has_edge(su, sv):
            sector_graph[su][sv]["weight"] += 1
        else:
            sector_graph.add_edge(su, sv, weight=1)

    short = {
        "Information Technology": "IT",
        "Oil Gas & Consumable Fuels": "Oil & Gas",
        "Automobile and Auto Components": "Auto",
        "Fast Moving Consumer Goods": "FMCG",
        "Financial Services": "Financials",
        "Construction Materials": "Constr. materials",
        "Consumer Durables": "Cons. durables",
        "Consumer Services": "Cons. services",
        "Metals & Mining": "Metals",
        "Telecommunication": "Telecom",
        "Capital Goods": "Capital goods",
    }
    angles = np.linspace(0, 2 * np.pi, len(sector_list), endpoint=False)
    pos_a = {s: (float(np.cos(a)), float(np.sin(a)))
             for s, a in zip(sector_list, angles)}
    weights = np.array([d["weight"] for _, _, d in sector_graph.edges(data=True)])
    max_weight = weights.max() if len(weights) else 1
    edge_widths = 0.3 + 2.6 * np.sqrt(weights / max_weight)
    edge_alphas = 0.06 + 0.38 * np.sqrt(weights / max_weight)

    # --- Panel (b): giant component with a readable hub backbone -------------
    giant = max(nx.connected_components(graph), key=len)
    hub_graph = graph.subgraph(giant).copy()
    hub_nodes = [n for n, _ in sorted(hub_graph.degree, key=lambda kv: kv[1],
                                      reverse=True)[:60]]
    hub_set = set(hub_nodes)
    backbone = hub_graph.subgraph(hub_nodes).copy()
    pos_b = nx.spring_layout(backbone, seed=config.RANDOM_SEED,
                             k=1.1 / np.sqrt(backbone.number_of_nodes()),
                             iterations=500)
    bx = float(np.mean([p[0] for p in pos_b.values()]))
    by = float(np.mean([p[1] for p in pos_b.values()]))
    radius = max(np.hypot(x - bx, y - by) for x, y in pos_b.values())

    # Place the remaining stocks near their neighbours so all 150 nodes appear.
    rng = np.random.default_rng(config.RANDOM_SEED)
    for node in hub_graph.nodes():
        if node in hub_set:
            continue
        placed = [pos_b[nb] for nb in hub_graph.neighbors(node) if nb in pos_b]
        if placed:
            pos_b[node] = (float(np.mean([p[0] for p in placed]) + rng.normal(0, 0.04)),
                           float(np.mean([p[1] for p in placed]) + rng.normal(0, 0.04)))
        else:
            theta = float(rng.uniform(0, 2 * np.pi))
            pos_b[node] = (bx + 1.05 * radius * np.cos(theta),
                           by + 1.05 * radius * np.sin(theta))

    hub_edges = [(u, v) for u, v in hub_graph.edges()
                 if u in hub_set and v in hub_set]
    top_hubs = [n for n, _ in sorted(hub_graph.degree, key=lambda kv: kv[1],
                                     reverse=True)[:10]]

    fig, (ax_a, ax_b) = plt.subplots(
        1, 2, figsize=(18, 8.5), gridspec_kw={"width_ratios": [1.0, 1.15]})

    nx.draw_networkx_edges(sector_graph, pos_a, ax=ax_a, width=edge_widths,
                           alpha=edge_alphas, edge_color="#777777")
    nx.draw_networkx_nodes(
        sector_graph, pos_a, ax=ax_a,
        node_size=[120 + 22 * sector_graph.nodes[s]["stocks"] for s in sector_graph],
        node_color=[colours[s] for s in sector_graph],
        edgecolors="white", linewidths=0.8)
    for name, (x, y) in pos_a.items():
        ax_a.text(1.18 * x, 1.18 * y, short.get(name, name),
                  fontsize=8, fontweight="bold",
                  ha="left" if x > 0.25 else ("right" if x < -0.25 else "center"),
                  va="bottom" if y > 0.25 else ("top" if y < -0.25 else "center"),
                  bbox=dict(facecolor="white", edgecolor="none",
                            alpha=0.75, pad=0.15))
    ax_a.set_xlim(-1.45, 1.45)
    ax_a.set_ylim(-1.45, 1.45)
    ax_a.set_aspect("equal")
    ax_a.set_title("(a) Sector-level network", fontsize=12)
    ax_a.axis("off")

    nx.draw_networkx_edges(hub_graph, pos_b, ax=ax_b, alpha=0.025,
                           width=0.2, edge_color="#b0b0b0")
    nx.draw_networkx_edges(hub_graph, pos_b, ax=ax_b, edgelist=hub_edges,
                           alpha=0.10, width=0.3, edge_color="#8a8a8a")
    other_nodes = [n for n in hub_graph.nodes() if n not in hub_set]
    nx.draw_networkx_nodes(hub_graph, pos_b, ax=ax_b, nodelist=other_nodes,
                           node_size=14, node_color="#c9c9c9",
                           edgecolors="none")
    nx.draw_networkx_nodes(
        hub_graph, pos_b, ax=ax_b, nodelist=hub_nodes,
        node_size=[40 + 10 * hub_graph.degree(n) for n in hub_nodes],
        node_color=[colours[hub_graph.nodes[n]["sector"]] for n in hub_nodes],
        edgecolors="white", linewidths=0.4)

    hub_angles = np.array([np.arctan2(pos_b[n][1] - by, pos_b[n][0] - bx)
                           for n in top_hubs])
    label_order = np.argsort(hub_angles)
    label_radius = radius * 1.30
    for rank, index in enumerate(label_order):
        node = top_hubs[index]
        theta = 2 * np.pi * rank / len(top_hubs) - np.pi / 2
        ax_b.annotate(
            hub_graph.nodes[node].get("symbol", node),
            xy=pos_b[node],
            xytext=(bx + label_radius * np.cos(theta),
                    by + label_radius * np.sin(theta)),
            textcoords="data", fontsize=7.5, fontweight="bold",
            ha="left" if np.cos(theta) > 0.2 else ("right" if np.cos(theta) < -0.2 else "center"),
            va="center", annotation_clip=False,
            bbox=dict(facecolor="white", edgecolor="none", alpha=0.85, pad=0.1),
            arrowprops=dict(arrowstyle="-", lw=0.5, color="#555555",
                            shrinkA=2, shrinkB=4))
    ax_b.set_title(f"(b) Giant component ({len(giant)} stocks)", fontsize=12)
    ax_b.set_aspect("equal")
    ax_b.axis("off")

    fig.suptitle(f"Nifty 200 correlation network at r = {threshold:.2f}",
                 fontsize=14)
    fig.tight_layout()
    save_figure(fig, "network_sectors.png", dpi=220)


# --------------------------------------------------------------------------- D
def sensitivity_analysis(corr: pd.DataFrame, threshold: float) -> None:
    log("D: threshold sensitivity")
    values = corr.to_numpy()
    rows = []
    for r in config.SWEEP_THRESHOLDS:
        graph = nx.from_numpy_array(adjacency(values, r))
        metrics = graph_metrics(graph)
        largest = max(nx.connected_components(graph), key=len)
        subgraph = graph.subgraph(largest)
        path = (nx.average_shortest_path_length(subgraph) if subgraph.number_of_nodes() > 1
                else np.nan)
        rows.append({"threshold": r, **metrics, "avg_path_length_giant": path})
    df = pd.DataFrame(rows)
    df.to_csv(config.RESULTS_DIR / "threshold_sensitivity.csv", index=False)

    fig, axes = plt.subplots(2, 2, figsize=(12, 9))
    panels = [
        ("edges", "Number of edges", "#3b6fb6"),
        ("avg_path_length_giant", "Avg. shortest path (giant)", "#c44e52"),
        ("giant_fraction", "Giant component fraction", "#55a868"),
        ("isolates", "Isolated nodes", "#8172b3"),
    ]
    for ax, (column, label, colour) in zip(axes.ravel(), panels):
        ax.plot(df["threshold"], df[column], "o-", color=colour)
        ax.axvline(threshold, color="grey", linestyle="--", linewidth=1,
                   label=f"primary r = {threshold:.2f}")
        ax.set(xlabel="Correlation threshold r", ylabel=label, title=label)
        ax.legend(fontsize=8)
    fig.suptitle("Sensitivity of network structure to the correlation threshold", fontsize=14)
    fig.tight_layout()
    save_figure(fig, "threshold_sensitivity.png")


def main() -> None:
    ensure_dirs()
    setup_plotting()
    graph, corr = load_graph()
    threshold = primary_threshold()
    degree_analysis(graph)
    centrality_analysis(graph)
    clustering_analysis(graph, threshold)
    sensitivity_analysis(corr, threshold)
    log("All analyses complete")


if __name__ == "__main__":
    main()
