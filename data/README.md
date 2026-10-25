# Input datasets

- `LiveTable100.ods`: official UK government Dwelling Stock Table 100, from the source file supplied in the user's Drive (`Total current housing capacity` folder).
- `london_dwelling_stock_2012_2025.csv`: exact borough/year values extracted from the source ODS by `../prepare_data.py` for the 33 London local authority codes (`E090...`).

The CSV contains no fabricated observations and uses the source's official tenure/provider categories, **not** an inferred owner-occupied/private-rented breakdown. The housing stock includes vacant dwellings.

To replace `LiveTable100.ods` with a new official version, update `prepare_data.py`'s year range if necessary and rerun it.

## v5 additional curated extracts

- `london_purchase_prices_by_type.csv`: monthly London-wide **purchase price estimates** for detached, semi-detached, terraced and flats/maisonettes; source: **UK House Price Index**, supplied workbook's `By type` worksheet. **Not** type-specific sales counts.
- `borough_sales_volume.csv`: monthly **total residential sales** by the 33 London authority codes from the same workbook's `Sales Volume` worksheet. **Not** a property-type split; recent registrations may be revised.
- `ons_2024_dwelling_tenure.csv`: optional, validated ONS 2024 borough dwelling-tenure extract, created using the official spreadsheet; must include code, borough, tenure, dwellings, year. The app can alternatively download the workbook or load it from `data/raw/subnationaldwellingsbytenure2024.xlsx`. The original 2021 London household-tenure chart/data have been removed.
- `borough_accommodation_types_census2021.csv`, `borough_tenure_census2021.csv`, `borough_population_2021.csv` and `borough_overcrowding_census2021.csv` are **optional** and are **not present** until generated from authoritative 2021 ONS borough-level CSVs with `../scripts/import_census_london.py`. Missing data are never guessed.

The source HPI workbook is preserved in `sources/UK_House_Price_Index.xlsx`. Script `../scripts/extract_hpi_extra.py` documents how the new HPI extras were extracted (uses `artifact_tool`; not required to run the Streamlit app).
