# Validation — Streamlit v3

- **Objective 1:** existing code, housing-stock CSV, methodology and boundary validation maintained from the v2 project.
- **Objective 2 sources:** imported directly from the Excel workbooks in Google Drive, using their sheet structure and official local authority GSS codes.
- **House-price observations:** 12,886 records (= 34 geographies × 379 months), January 1995 to July 2026. All 33 borough/City codes plus London regional code `E12000007`.
- **Private-rent observations:** 4,620 records (= 33 geographies × 140 months), January 2015 to August 2026. The 32 boroughs except City of London plus London regional code `E12000007`.
- **London regional benchmark** comes directly from each published London row; not averaged from borough prices.
- **Rent YoY** uses source-provided percentage, while **HPI YoY** uses the same borough's modelled average price in the corresponding month of the previous year.
- **Missing rent for City of London** is treated as missing, never 0. A grey map polygon is explicitly drawn for that city when geometry is available.
- **CSV join keys** match Objective 1 stock data by nine-character GSS local-authority code.
- **Unit tests:** 4 data/chart-construction tests passed. Browser-only preview was run with headless Chromium: both tabs and a borough change showed real figures without JavaScript exceptions.
- **Not yet tested:** actual Streamlit server launch; package installation was prevented by external DNS restrictions. Boundary data could not be downloaded in this environment; app supports official remote loading, caching and GeoJSON upload fallback.

## Objective 3 · 18 October 2026
- Added A1, A2P/A2R and TA1 extraction from four locally provided 2025 MHCLG quarterly ODS files.
- Added CHAIN P1 extraction for eight quarters through 2026–27 Q1.
- Added GLA/EHS regional (not borough) overcrowding historical context, from *Housing in London 2025* sheet 4.9.
- 136 statutory records (33 authorities + London, four quarters); 3,536 homelessness-reason rows; 272 CHAIN P1 records.
- 2025 Q4 published London values checked: 16,290 households owed duty, 6,540 prevention, 9,750 relief, 75,600 households in TA, 100,930 children in TA, 21.1455 TA households per 1,000 households.
- CHAIN P1 published 2026–27 Q1 London value checked: 3,959 people seen rough sleeping.
- Missing December 2025 TA local returns: Brent and Ealing remain NULL (not zero). Other quarter-specific missing returns also retained.
- Five Objective 3-specific unit tests passed; whole project suite 14 tests passed (9 pre-existing and 5 Objective 3 tests).
- Static screenshot generated from actual source values. Streamlit server unavailable in model runtime, so a live interactive Streamlit UI remains to be verified on user's local machine.
- Raw Table 600 and Census TS052 download attempts blocked from sandbox. No borough waiting-list or Census overcrowding numbers have been invented. Source links and an optional local downloader are included.

## v5 review-file changes (2026-10-22)

- Implemented a cross-section source glossary and precise interpretation notes for stock, provider categories, duties, temporary accommodation and rough sleeping.
- Added 2021 regional occupied-household tenure context from ONS Census TS054; verified total of 3,423,889 households. **Do not compare as if it were a decomposition of 2025 dwelling stock.**
- Added UK HPI `By type` London-wide price extracts through July 2026, and `Sales Volume` borough totals through June 2026, without inferring property-type transaction counts.
- Removed all Streamlit `download_button` controls, moved rent benchmark labelling into a caption to prevent chart overlap and lightened map background colours.
- Added source-bounded offline Q&A and optional OpenAI API mode; no keys included; no browsing, missing data or modelled causal impacts are fabricated.
- Borough-level 2021 ONS accommodation, tenure, overcrowding and population charts only activate after validated 33-area official CSV imports. Unavailable files remain unavailable.
- No official borough geometry could be retrieved in the authoring environment. Scripts to download/validate precise 33 GLA polygons are retained; corresponding maps remain dependent on official data, not invented shapes.
- Automated tests: 20 passed (`python -m pytest -q`); static module compilation passed. **Live Streamlit browser execution was not performed in the authoring environment**, where Streamlit is not installed. Users should run `python -m pip install -r requirements.txt` locally.
