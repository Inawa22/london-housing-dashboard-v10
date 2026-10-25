# London Housing Capacity Dashboard

An interactive **Streamlit prototype** investigating London's existing housing stock, housing costs, and indicators of unmet housing need across its local authorities.

> **Status:** v6, evidence-first hypothesis-testing prototype with detailed Objectives **1–3**. Objective 4 (the effects of adding homes on housing costs and unmet need) is **not yet implemented**. Do not interpret these descriptive data as causal estimates.

## Run locally

Requires Python 3.10+.

```bash
python -m venv .venv
# Windows (PowerShell): .\.venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Open the URL Streamlit prints (usually `http://localhost:8501`). Use **Dashboard section** in the sidebar to move between objectives.

## New starting point: testing the core research hypothesis

The default navigation item is now **🔎 · Test the hypothesis**. This reframes the dashboard around the client's research question: **is London adding enough homes to meet assessed housing need, and what can the evidence tell us about costs and unmet need?**

- **01 · Test the supply gap:** 2024–25 official London **net additions (32,680)** compared with a selectable annual benchmark (**~88,000** under the government standard method by default, with distinct historical GLA SHMA and London Plan benchmarks clearly labelled). Presents the *annual benchmark difference* with sourcing and limitations.
- **02 · What pressure looks like:** official 2025 temporary-accommodation households and the ONS modelled London rent time series. Counts and time periods are clearly separated.
- **03 · Borough evidence:** exploratory scatter of 2012–25 growth in existing dwelling stock and 2025 Q4 temporary-accommodation household rates, connected by exact GSS codes, preserving missing borough returns. Highlights the Newham example without causal claims.
- **04 · Definitions & reliability:** explains housing stock versus supply flow, annual need estimate versus observed demand, and costs versus affordability, including source quality and unresolved questions.

**Presentation support:** [`SATURDAY_PRESENTATION_BRIEF.md`](SATURDAY_PRESENTATION_BRIEF.md) provides a four-to-six-minute verbal walkthrough, careful wording, a source/reliability table and questions to ask the client. [`HYPOTHESIS_WORKPLAN.md`](HYPOTHESIS_WORKPLAN.md) lists which propositions the data support, do not support, or contradict, and identifies what's required for a proper long-term test.

**Current supported result, bounded:** in FY2024–25, 32,680 net additional homes were recorded in London, compared with an approximate modelled annual requirement of 88,000 under a different planning methodology (about 37% delivery relative to that benchmark). **This is not a measured historical demand gap, a count of households without homes, or a causal estimate.**

## Dashboard sections

### 1 — Current housing capacity (existing dwelling stock)

- London-wide and selected-borough KPI cards, borough ranking, stock by **sector**, and historical trends.
- Borough choropleth with a light background, auto-loading verified borough boundaries when available.
- **2024 ONS dwelling-tenure donut**, replacing the 2021 Census household-tenure chart. Select all London or an individual borough; the four groups are owned outright, owned with a mortgage, private rent, and social rent. Data are fetched from the official workbook when available, or can be uploaded; nothing is invented if the source is unavailable.
- Optional Census 2021 borough **accommodation-type** charts remain separate, with their reference year clearly shown.
- Source: MHCLG **Live Table 100**; 2012–2025 snapshot included.
- **Interpretation:** dwelling stock includes owner-occupied, rented and vacant homes; sector is *not* the same as household tenure. Total and private-sector values are estimates, not accurate to the nearest individual dwelling; recent years are provisional.

### 2 — Cost of housing

- Separate **Renting** and **Buying** tabs, monthly price/rent KPI cards, London regional comparisons, borough rankings, historical trends, bedroom rents and choropleths.
- **Renting by property type** for the selected area, **buying price by type** for London as a whole, and **borough total property sales volumes** for complete years (extracted from the supplied HPI workbook). Property-type **prices do not count** most popular types.
- Sources: ONS **Price Index of Private Rents (PIPR)** and **UK House Price Index (HPI)**.
- Snapshot coverage: rents January 2015–August 2026 (32 boroughs plus separately published London regional figures); prices January 1995–July 2026 (33 London authorities plus London regional figures).
- The London reference line uses the **published regional series**, not a simple average across boroughs. City of London has no separate rental series and is treated as missing, not zero.
- Note: housing costs are **not** affordability measures without income information.

### 3 — Unmet housing demand: indicators of housing need

- **Homelessness & temporary accommodation:** MHCLG quarterly duties, prevention versus relief, households in temporary accommodation, children, reasons, local-authority rates and trends.
- **Rough sleeping:** CHAIN people seen rough sleeping by time and area, separate from household-based counts.
- **Wider housing need:** GLA London-wide overcrowding context and optional borough ONS Census TS052 overcrowding data.  Borough-level social housing waiting-list and Census overcrowding charts are **pending** appropriate validated datasets. The code exposes the expected CSV schema in `OBJECTIVE3_SOURCES.md`.
- The provided statutory homelessness data cover the four quarters of **2025**; CHAIN includes **2026–27 Q1**. These sources have different reporting periods and counting units.
- Do not add these overlapping categories to infer a single "total unmet demand" figure. Some council returns are missing, and published regional totals can include adjustments.

### Ask the data

Select **“💬 · Ask the data”** in the sidebar for source-grounded questions.

- Default **offline mode** answers predefined housing-stock, costs, homelessness, rough-sleeping and definitions questions using **bundled data and citations**. This is a rules-based data assistant, *not* an AI language model.
- Optional **AI mode**: copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and set `OPENAI_API_KEY` to an OpenAI API key (separately billed). AI answers receive the selected area's **aggregated numeric facts**, source links and clear data limitations—not the original workbooks or private user records. A connection is required; the API is not a live dataset search. Only include data/questions you're comfortable sending to the configured API. The key is gitignored.
- Responses may still require checking: they never substitute for the original source tables.

### Add validated Census borough data

The ONS publishes Census 2021 borough statistics for [accommodation type TS044](https://www.ons.gov.uk/datasets/TS044/editions/2021/versions/4), [overcrowding TS052](https://www.ons.gov.uk/datasets/TS052/editions/2021/versions/5), [population TS001](https://www.ons.gov.uk/datasets/TS001) and [household tenure TS054](https://www.ons.gov.uk/datasets/TS054). After downloading the corresponding **official local-authority CSVs**, import as follows:

```powershell
python scripts/import_census_london.py --ts044 data/raw/TS044.csv --ts052 data/raw/TS052.csv --ts001 data/raw/TS001.csv --ts054 data/raw/TS054.csv
```

Only fully validated 33-borough files activate additional charts. The default archive **does not contain these datasets**. An ONS 2021 population denominator can be used with **2021** dwelling stock, not with the 2025 stock figure. [MHCLG Table 600 housing registers](https://www.gov.uk/government/statistical-data-sets/live-tables-on-rents-lettings-and-tenancies) is separately pending.

## Repository structure

| File or folder | Purpose |
|---|---|
| `app.py` | Streamlit entry point, navigation and Objective 1 |
| `hypothesis_dashboard.py` | Evidence-first hypothesis testing introduction with sources and caveats |
| `cost_dashboard.py` | Objective 2 |
| `unmet_dashboard.py` | Objective 3 |
| `housing_assistant.py`, `housing_explainer.py` | Optional AI/offline Q&A, glossary and source reliability descriptions |
| `boundaries.py`, `download_boundaries.py` | Official London borough geometry and validation |
| `data/*.csv` | Curated datasets needed to run the dashboard offline (except first-use map boundaries). v6 also adds sourced annual-delivery and benchmark tables. |
| `data/LiveTable100.ods`, `data/sources/` | Provided original government/CHAIN/GLA workbook snapshots for provenance and extraction |
| `scripts/` | Data preparation, extraction and optional official-source download scripts |
| `tests/` | Source coverage, data calculations and boundary validation tests |
| `OBJECTIVE3_SOURCES.md`, `REVIEW_NOTES_v5.md` | Data provenance, methodology, feedback checklist and remaining data needs |
| `VALIDATION.md` | Validation notes |

The original 18 MB ONS rents workbook and original HPI workbook are **not** required at runtime: processed extracts are included. HPI **London purchase prices by property type and borough total sales volumes** were additionally extracted directly from the supplied workbook, with reproducible script `scripts/extract_hpi_extra.py`. To rerun the Objective 2 extraction, download those original workbooks from their public publishers (or the research Drive folder), place them in `data/raw/`, and run `python scripts/extract_from_workbooks.py`.

Large HTML previews, downloaded map caches, local secrets and virtual environments are excluded from Git. The dashboard itself contains the live visualisations.

## Borough maps

Borough maps use London geographic boundary data, joined using official nine-character GSS area codes. On first use the app attempts to fetch and cache the borough GeoJSON. If the service is unavailable, other charts continue working. For a reliably offline map, run `python download_boundaries.py` while connected and copy the generated `data/london_boroughs.geojson` file into the project on the computer where you run Streamlit. The map should not be described as bundled/offline until this file is present. Real polygon geometry is not fabricated.

## Data caveats and sources

- **Dwelling stock:** [MHCLG Live Tables on Dwelling Stock](https://www.gov.uk/government/statistical-data-sets/live-tables-on-dwelling-stock-including-vacants).
- **House prices:** [UK House Price Index](https://www.gov.uk/government/collections/uk-house-price-index-reports).
- **Private rents:** [ONS PIPR](https://www.ons.gov.uk/economy/inflationandpriceindices/datasets/priceindexofprivaterentsukmonthlypricestatistics).
- **Statutory homelessness:** [MHCLG homelessness live tables](https://www.gov.uk/government/statistical-data-sets/live-tables-on-homelessness).
- **Rough sleeping:** [GLA CHAIN reports](https://data.london.gov.uk/dataset/rough-sleeping-in-london-chain-reports-2n88x).
- **Boundary geometry:** [GLA borough boundaries](https://data.london.gov.uk/dataset/london-boroughs-e55pw).
- **Additional wider-need sources / detailed caveats:** see [`OBJECTIVE3_SOURCES.md`](OBJECTIVE3_SOURCES.md).

Original data in this snapshot may have been revised by publishers after extraction. In particular, some revised statutory homelessness 2025 releases and 2026 data are **not** yet incorporated. The app should therefore be described as a historical research prototype, not a live official reporting service.

## Tests

```bash
python -m pip install -r requirements.txt pytest
python -m pytest -q
```

The repository has data/code tests but the live Streamlit UI still needs an end-to-end browser test on a machine with Streamlit and internet access for boundary loading.

## Planned Objective 4

An explicitly assumption-based scenario simulator exploring additional dwelling supply versus estimated changes in housing cost and unmet demand. Not part of this release. Any modelling must clearly separate observed data from simulated outcomes.

## Licence

No licence has yet been selected for the application's own code. The linked public datasets remain subject to their respective publishers' terms. Choose a code licence before declaring the repository open for reuse.

### v10: Income and wider housing need

Objective 2 now includes a **💷 Income** tab with London-wide 2026 PAYE monthly pay, 2025 residence-based full-time ASHE borough earnings (converted to monthly equivalents), the GLA historical London earnings/rent trend and a separate pay-vs-rent illustration. Objective 3 includes real 2024 London borough housing-register figures and sourced 2025/2021 London-wide waiting-list/overcrowding headline measures. For limitations and exact sources see [`INCOME_AND_DEMAND_NOTES_v10.md`](INCOME_AND_DEMAND_NOTES_v10.md).
