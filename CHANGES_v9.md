# v9 — Remove unpopulated wider-housing-need panels

- Removed the public-facing **Social housing waiting lists — additional borough dataset required** placeholder, including its external source button and CSV formatting instructions.
- Removed the **Overcrowding by borough — Census 2021 source pending** placeholder, including its external source button and CSV formatting instructions.
- Both borough-level charts will still display automatically if validated CSV files become available; no additional data are invented.
- Kept the London-wide overcrowding trend (based on the GLA/English Housing Survey), homelessness and rough-sleeping views, and Objective 1's ONS 2024 tenure donut.
- Reworded the wider-need tab introduction, and removed the future-datasets to-do message in the user-facing tab and reference guide.
- Added a regression test preventing the two pending-data messages from reappearing.

Run: `python -m pip install -r requirements.txt` then `python -m streamlit run app.py`.
