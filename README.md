# Nifty 200 correlation network — assignment pipeline

Reproducible pipeline for the ECS414/614 Network Science assignment:
"Topological & Structural Analysis of the Indian Stock Market".

## Environment

A virtual environment already exists in `assignment/`. It was used for all
results; `requirements.txt` is a frozen snapshot of its packages. Missing
extras (`scipy`, `matplotlib`, `seaborn`, `jinja2`) have been installed into it.

```bash
# from this folder
assignment/bin/python -m pip install -r requirements.txt   # only needed on a fresh machine
```

## Run order

```bash
assignment/bin/python src/00_fetch_data.py      # yfinance -> data/prices_raw.csv (run once)
assignment/bin/python src/01_preprocess.py      # -> data/derived/{prices_aligned,log_returns,correlation}.csv
assignment/bin/python src/02_build_network.py   # -> data/derived/graph_primary.graphml + threshold scan
assignment/bin/python src/03_analyses.py        # -> report/figures/*.png + data/derived/results/*.csv
assignment/bin/python src/04_report_tables.py   # -> report/tables/*.tex
```

Only step 0 needs internet access. Its outputs are cached, so later runs are
offline and deterministic. `config.py` holds all parameters (period, coverage,
thresholds, seed).

## Data format

- Input: `ind_nifty200list.csv` (columns `Company Name, Industry, Symbol, Series, ISIN Code`).
  Yahoo tickers are formed by appending `.NS` to `Symbol`.
- `data/prices_raw.csv`: dates as rows, one column per ticker, adjusted close
  (`yfinance` `auto_adjust=True`).
- Derived files and all metric tables are under `data/derived/`.

## Report

`report/main.tex` is the LaTeX source. It is self-contained with its
subfolders: keep `report/figures/` and `report/tables/` next to `main.tex`.

To compile locally:

```bash
cd report && pdflatex main.tex
```

On Overleaf, upload the whole `report/` folder and set `main.tex` as the main
document (tables and figures are included with relative paths).
