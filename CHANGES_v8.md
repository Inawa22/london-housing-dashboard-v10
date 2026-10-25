# v8 — 2024 ONS dwelling-tenure replacement

- Removed the old Census 2021 regional **household tenure** chart from Objective 1 and removed its unused extracted CSV from the project. The Ask the Data assistant no longer supplies the old 2021 figures as current tenure evidence.
- Added a four-segment **2024 ONS dwellings by tenure** donut: owned outright; owned with a mortgage/loan; privately rented; socially rented. Works for all London or a selected local authority, using GSS codes. Includes hover counts and percentages, a simple accompanying table and an official ONS source link.
- No numeric 2024 ONS values were fabricated. The ONS Excel download was blocked from the preparation environment. The app tries the official ONS download on the user's computer; a validated `data/ons_2024_dwelling_tenure.csv` or official workbook at `data/raw/subnationaldwellingsbytenure2024.xlsx` also works. If unavailable, the app offers a file upload and explains why the chart is not populated yet.
- Included `tenure_2024.py` for workbook importing, data validation, and strict handling of percentages, dates, local-authority coverage and categories; added `openpyxl` dependency and automated tests.
- Kept all other substantive housing views. The request to remove unspecified "cards" awaits identification (screenshot or exact card titles); none were deleted without knowing which were intended.

## Official data source

ONS, *Subnational estimates of dwellings by tenure, England*, current 2024 edition, published 11 February 2026: https://www.ons.gov.uk/peoplepopulationandcommunity/housing/datasets/subnationaldwellingstockbytenureestimates

ONS method: small area SPREE estimates, based on Census 2021, Labour Force Survey and government administrative dwelling-stock records. Data are 2024 **dwelling estimates**, not household counts; should not be mistaken for exactly measured vacancies or the 2025 government provider categories.

## Run

```
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

If the donut does not appear, download the 2024 dwelling (NOT household) `.xlsx` from the ONS link and upload it in Objective 1 or save under `data/raw/subnationaldwellingsbytenure2024.xlsx` then restart.
