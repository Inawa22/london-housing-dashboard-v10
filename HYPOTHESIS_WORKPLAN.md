# Research architecture: from description to a testable housing hypothesis

The dashboard's hypothesis-first page is a new **entry point**; the detailed Objectives 1, 2 and 3 remain available as drill-down views. Objective 4 is **not** implemented.

## Claims, evidence and statuses

| Proposed hypothesis component | What the present data can show | Status |
|---|---|---|
| London adds fewer homes per year than it needs | 2024–25 MHCLG net additions versus selected annual planning need or target | **Indicative support for a single-year planning shortfall**; need estimate is modelled and method-sensitive |
| Need has *consistently* exceeded supply over time | Would require a comparable multiyear series for **both** delivery and need | **Not yet tested** (no constructed constant-method need series included) |
| The overall stock did not increase | Official dwelling stock rose 13.8% from 2012 to 2025 | **Contradicted** by data; but this does not falsify a need-versus-delivery gap |
| More stock implies less local homelessness | Borough stock growth against the 2025 Q4 rate of households in temporary accommodation | **Cannot be established causally**; Newham is a useful counterexample to simplistic expectations |
| Supply shortage causes high rents | Costs rise over time but without controls for incomes, rates, population shifts etc. | **Not established**; requires explicit modelling |
| A specified additional supply reduces rents or homelessness | No causal elasticity or counterfactual is estimated | **Objective 4 pending** |

## Why “demand > supply” is challenging to identify

Economic demand is a function of price and income, not one observed number. Population is not households; recorded households are not all the households who *would* form if homes were affordable; planning housing need is a model, not an observed purchase/tenancy market. Existing total stock includes unavailable occupied homes. A borough can have thousands of new dwellings and still have a shortage of accessible social-rent homes.

For rigorous testing, we should align **geography**, **calendar or financial year**, **units (households/dwellings/people)**, **definition** and **statistical vintages**. Do not aggregate a CHAIN person count with a statutory homelessness household count.

## Priority next datasets (not yet bundled)

1. **Annual net housing supply 2000–2025**, official MHCLG Table 109 and local-authority data. The 2024–25 observed net additions are already included as a verified one-year point. Comparing stock changes is a secondary check, not a substitute for annual net-supply outturns.
2. **Time-consistent housing need series:** GLA SHMA assumptions or reconstruct comparable annual need using household projections and backlog; do not silently carry 2024's 88k requirement back to 2012.
3. **Housing register Table 600**, borough/year; registers are policy-sensitive and not a count of unique households across boroughs.
4. **ONS Census TS052 overcrowding / TS044 accommodation / TS054 tenure** across all London local authorities for the same year; derive shares by denominator, note 2021 pandemic and Census timing.
5. **ONS/GLA household income and rental affordability** to distinguish nominal costs from affordability; add mortgage rates for price trends.
6. **Affordable and social housing net additions / lettings / turnover** because “total homes” does not show the tenure of supply accessible to those in greatest need.

## Analytical approach for Objective 4 later

Start with a transparency-first **scenario calculator** reporting model assumptions explicitly, then estimate a credible supply-rent response from published elasticity studies or a carefully designed panel model with borough and year fixed effects, covariates and sensitivity checks. Do not fit a causal relationship to the exploratory stock-growth versus TA scatter alone. For TA outcomes, separate affordable housing allocations from private market completions and respect outcome lags. Report ranges, not spurious point precision.

## Presentation discipline

Use one result per view. Always state **what it means, what it does not mean, and the next test**. For clarity:

- “A 55,320-home shortfall” is **only** a *single-year difference against a selected annual benchmark* — not an accumulated housing deficit or an observed waiting list.
- “London is undersupplied” is stronger than current evidence supports unless bounded to “delivery falls below the modelled annual housing requirement for 2024–25.”
- “More homes didn't help Newham” is not evidenced; observed housing need might have been substantially worse without new dwellings.
