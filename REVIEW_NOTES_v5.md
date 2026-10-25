# Dashboard revisions from “Promp Chatgpt for dashboard.docx” (v5)

This file records the change requested, implementation and remaining data boundaries.

| Page / request | Result |
|---|---|
| p1 — definitions (housing capacity, stock, dwelling, boundaries, TA, duties, types) | Implemented expandable definitions and linked source/reliability guide on Objectives 1–3; assistant answers definitions. |
| p1 — sources and why reliable | Implemented source/publisher/evidence/limitation list with official links. |
| p1 — bar hover shows existing dwelling count | Implemented explicit viewer instruction; existing Plotly tooltips already display count. |
| p2 — donut hover shows percentage and count | Implemented instruction; existing Plotly donut tooltip already displayed percentages and count. |
| p2 — 78.5% private-sector interpretation | Corrected misleading causal inference. “Private sector” includes owner-occupied **and** private rented dwellings, is an ownership/provider category, and is not a measure of prices or tenancy shares. |
| p2 — go deeper on council/housing-association/other public stock | Full explanation below, without adding unsupported claims to the dashboard. |
| p2 — lighter borough-map background | Light blue-grey Plotly geo/paper background, no blue sea treatment. |
| p3 — private sector owner's tenure vs private rent | New **London-wide ONS Census 2021 TS054** chart (occupied households), clearly separate from 2025 Table 100 provider stock; optional borough TS054 importer. |
| p3 — dwellings per 1,000 residents | Never use invented denominator. For genuine 2021 33-borough ONS TS001 population CSV, importer prepares `data/borough_population_2021.csv`; matching 2021 stock uses 2021 census only. |
| p3 — why detached rent can fall below semi-detached | Explained the descriptive price-level comparison and non-like-for-like mixes; clarified modelled price ≠ counts/transactions. |
| p3 — remove all download buttons | Removed all `st.download_button`s from the current dashboard; official source links remain. |
| p3 — AI to answer source-based questions | Added “Ask the data” section: source-grounded offline answers (no key), and optional real API-powered text generation if `OPENAI_API_KEY` is configured privately. API receives aggregated dataset context, not raw uploaded records. It is not live web search. |
| p3/4 — underhoused households | Explained as Census 2021 bedroom-standard overcrowding; London-wide existing regional historical indicator retained. Borough-level chart activates only with validated ONS TS052 CSV; importer included. |
| p3/4 — property types and popularity | Added London-wide **UK HPI By type prices**, borough-wide **total sales volumes** from the supplied original workbook, and already available ONS property-type rents by chosen borough. These sources **do not** give transaction counts by property type, therefore “most bought/rented type” cannot be inferred. Optional ONS Census TS044 accommodation-type distribution for 2021 can be imported (not a popularity count). |
| p4 — temporary-accommodation “burden” wording | Renamed to “Where is temporary accommodation most widely used?” and clarified absolute count vs rate per 1,000 local households. |
| p4 — “Load map boundaries” button | Removed the checkbox; automatic official geometry loading plus clear fallback message. Map polygons still require a valid official GLA `data/london_boroughs.geojson`; no arbitrary polygons generated. |

## Why council, housing-association and other-public stock are **not** “available affordable homes”

- Table 100 counts **all existing dwellings by provider sector**, regardless of whether any individual dwelling is occupied, vacant, for rent, for sale or allocated to a new resident.
- Some dwellings owned by a public or social landlord have long-term tenants; their existence does **not** make them immediately available to another household. Similarly, some homes may be undergoing repairs or may be unavailable for use.
- Housing stock is a **point-in-time total**. To measure access, you would need data on **vacancies becoming available**, **new lettings**, **waiting lists**, **eligibility rules**, **bedroom sizes** and **actual rent burden**. Stock totals alone cannot supply that.
- “Council / housing association / other public” are **provider categories**, not an affordability guarantee. “Private sector” includes both owner-occupiers and private rentals. You cannot deduce a share of high-price housing from these provider shares.
- Census tenure (2021 occupied households) cannot be subtracted from provider-sector stock (2025 dwellings), because the units and reference dates differ. Small misclassification, Census disclosure adjustments and unit mismatch add further uncertainty.

## Data coverage and pending improvements

Already bundled: MHCLG Table 100 stock, ONS rents, HPI prices and sales volumes, MHCLG statutory homelessness, CHAIN rough sleeping, GLA regional overcrowding history, **London regional 2021 Census tenure categories**.

Additional official data identified but **not bundled as verified borough-level files**: [ONS TS044 accommodation type](https://www.ons.gov.uk/datasets/TS044/editions/2021/versions/4), [ONS TS052 occupancy rating](https://www.ons.gov.uk/datasets/TS052/editions/2021/versions/5), [ONS TS054 tenure](https://www.ons.gov.uk/datasets/TS054), [ONS TS001 population](https://www.ons.gov.uk/datasets/TS001), and [MHCLG waiting-list Table 600](https://www.gov.uk/government/statistical-data-sets/live-tables-on-rents-lettings-and-tenancies). See `scripts/import_census_london.py` for generating source-checked borough CSVs from official ONS downloads.

**Map geometry**: the dashboard loads and validates precisely 33 official borough GeoJSON features joined by GSS code. The checked-in project has no bundled borough GeoJSON because it could not be retrieved in the authoring environment. If the previous installation already cached `data/london_boroughs.geojson`, copy that verified file into the v5 project's `data/` folder. Otherwise, run `python download_boundaries.py` when internet is available. Do not fill map with synthetic geometry.

**Objective 4 is not implemented.** Historical descriptive figures are not automatically causal predictions of future costs or homelessness.
