# v7 — Plain-English housing comparison and source-label fix

## Fixed: the `000)` benchmark label bug

The previous `data/housing_need_benchmarks.csv` contained commas *inside* the `benchmark` names without enclosing the affected cells in quotes. `pandas.read_csv` silently treated the first part of each name as an index and parsed `benchmark` as `000)`. The issue was in the data, not merely the width of the Streamlit dropdown. We have reconstructed the original full names, written a correctly escaped CSV, and added a validation step and regression tests.

## Improved: the comparison screen

- Long text dropdown replaced with three short, horizontally arranged radio choices: Government method · 88k/year, GLA study · 66k/year and London Plan · 52k/year.
- Each choice maps to one and only one full record in the official-source CSV. If a name is damaged again, the app now raises an explicit error rather than quietly showing `000)`.
- The bar chart now names the *specific source* — e.g. `Government standard method (2024)` — rather than `Selected annual benchmark`.
- The adjacent KPI changes label to match the chosen estimate or policy target.
- Source-specific links updated to the GLA's 2024 standard-method analysis, the GLA's 2017 SHMA and the London Plan monitoring tables. A separate link explains the government's standard-method formula.
- Rewrote the introduction, section questions, findings and caveats in conversational, accessible English. The new wording still distinguishes **actual net additional homes** from **estimated annual housing need** and **policy targets**.
- This dashboard compares rounded values of 88,000 / 66,000 / 52,000. The official source figures are approximately 87,992 / 65,878 / 52,287 respectively. This is not an estimate of household applications or the accumulated housing backlog.

## Scope and testing

This release updates the hypothesis-first introductory section and its data/source labels, while retaining the existing housing-stock, cost, homelessness and assistant sections. Automated tests include regression checks for the labels, source links, selectable alternatives and figures. No live Streamlit browser test was performed in this environment.

## To run

```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```
