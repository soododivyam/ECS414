# Code snippets for the report

Drop-in, syntax-highlighted LaTeX snippets of the important parts of the
analysis pipeline. Each snippet is a `lstlisting` block using the shared
`python` style defined in the preamble of `report/main.tex`.

Source scripts live in `../src/`; each snippet header names the file it came
from.

## Files

| File | Contents | Suggested report placement |
|------|----------|----------------------------|
| `01_config.tex` | Period, coverage, threshold grid, sweep, seed | §2 Methodology (reproducibility) |
| `02_data_download.tex` | `yfinance` batch download and price cache | §2.1 Data source |
| `03_preprocess.tex` | Coverage filter, log returns, Pearson matrix, sanity checks | §2.1–2.2 (eqs. 1–2) |
| `04_threshold_selection.tex` | `graph_metrics` helper and `choose_threshold` | §2.2 Network construction |
| `05_build_network.tex` | Adjacency matrix and graph with node metadata | §2.2 (eq. 3) |
| `06_degree_distribution.tex` | Degree histogram and log–log fits | §3.2 Degree distribution |
| `07_centrality.tex` | Degree/betweenness/eigenvector centrality, Spearman | §3.3 Centrality |
| `08_clustering_homophily.tex` | Clustering, Erdős–Rényi baseline, homophily, modularity | §3.4 Clustering & homophily |
| `09_threshold_sensitivity.tex` | Threshold sweep and giant-component path length | §3.5 Threshold sensitivity |
| `10_network_layout.tex` | Spring layout, sector colours, node sizes | Figure 5 / §2.4 |
| `11_latex_tables.tex` | `pandas.to_latex` → `booktabs` export | §2.4 Code / appendix |
| `12_network_metrics.tex` | Concise NetworkX metric calls (moved from `main.tex`) | §2.4 Code |
| `00_all.tex` | Gallery that inputs every snippet above | Preview only |

## Usage

Include one snippet where you want it, for example in §3.3:

```latex
The code for the three centralities is:
\input{code/07_centrality}
```

`00_all.tex` already contains the `\input` lines if you prefer to preview
everything at once:

```latex
\input{code/00_all}
```

Compile from `report/` as usual (`cd report && pdflatex main.tex`); the paths
are relative to `main.tex`.

## Preamble

`report/main.tex` loads the highlighting setup (`xcolor`, `listings`, and the
`python` style). The relevant block is:

```latex
\usepackage{xcolor}
\usepackage{listings}

\definecolor{codebg}{HTML}{F7F7F7}
...
\lstdefinestyle{python}{ ... }
```

Keep `xcolor` before `hyperref`.

## Adding a caption / number

Add `caption` and `label` to the snippet's `lstlisting` options, e.g.:

```latex
\begin{lstlisting}[style=python,
  caption={Centrality computation with NetworkX.},
  label={lst:centrality}]
```

Then refer to it with `\ref{lst:centrality}` and, if you want a list of
listings, add `\lstlistoflistings` where appropriate. Without a `caption`
option the block stays inline and unnumbered, like the old `verbatim` block.

## Notes

- Long code lines wrap automatically (`breaklines=true`).
- Indentation is preserved (`keepspaces=true`, `columns=fullflexible`).
- Code is copied from the working pipeline; names such as `graph`,
  `config`, `values` and `sector_list` match the surrounding scripts.
- The snippets are excerpts, not runnable files. The complete scripts are in
  `../src/`.
