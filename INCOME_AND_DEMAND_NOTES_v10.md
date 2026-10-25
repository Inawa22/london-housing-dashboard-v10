# v10: Income and wider housing need — source notes

## New `💷 Income` tab under Objective 2

**Headline**: HMRC/ONS PAYE RTI September 2026 pay for employees living in London: median gross monthly pay **£3,120**; UK median **£2,660**, London annual change **+3.9%**. Source: [GLA Labour Market Update October 2026](https://data.london.gov.uk/download/v8wzm/q24/2026.10%20LMU.html), based on HMRC/ONS PAYE RTI. Latest UK and London PAYE are **employee** medians, not household income, net pay or the pay of renters specifically. August 2026 London PAYE median £3,118 is drawn from the [ONS September 2026 release](https://www.ons.gov.uk/employmentandlabourmarket/peopleinwork/earningsandworkinghours/bulletins/earningsandemploymentfrompayasyouearnrealtimeinformationuk/september2026). Latest payroll figures can be revised.

**Borough comparisons**: ONS ASHE 2025 median **gross weekly earnings of full-time workers by place of residence**, via Nomis official Labour Market Profiles. 32 boroughs, each linked to its source URL in `data/resident_fulltime_earnings_ashe_2025.csv`. City of London is excluded from this particular borough extract; the London region has its own official £902.70/week median, **not** an arithmetic average of borough medians. The monthly figure is *our own derived monthly equivalent*: weekly × 52 ÷ 12, which is approximately £3,912 for the London region. ASHE and PAYE are independent statistics covering different worker populations and years; do not describe them as estimates for the same group.

**Historical trend**: `data/london_pay_history_gla_2015_2025.csv` contains monthly GLA compiled pay and rent values transcribed from *Housing in London 2025*, worksheet/figure 3.11, January 2015–August 2025. The GLA report's original methodological caption describes a workplace-based earnings series, unlike the residence-based 2025 borough ASHE series. The 2026 PAYE series is shown separately, not spliced into the old GLA chart. It is also unsafe to assume the trends refer to the same workers or renters.

**Rent versus pay**: The side-by-side figures are separate medians and averages from different populations and reference months. Do **not** calculate a typical renter's rent-to-income ratio from the two marginal estimates or claim average monthly rent is a typical wage earner's housing cost.

## Waiting lists (Objective 3)

`data/borough_waiting_lists.csv` now contains 33 2024 borough counts transcribed from the map on p.26 of [London Assembly Affordable Housing Monitor 2025](https://www.london.gov.uk/sites/default/files/2025-07/Affordable%20Housing%20Monitor%202025_1.pdf), which cites MHCLG Table 600. These are **registration counts** and can include duplicates across boroughs, may be outdated and depend on register eligibility rules. **Note**: The map labels add to 336,366 and the report states a London total of 336,357, differing by 9 registrations; use the reported total rather than recalculating it from borough map labels. The v10 dashboard also quotes the separately verified London-wide March 2025 register total **341,421**, from [London Assembly Housing Committee report, March 2026](https://www.london.gov.uk/sites/default/files/2026-03/Housing%20Committee%20-%20Allocations%20in%20social%20housing%20report%20-%20FINAL.pdf). Never mislabel 2024 borough counts as 2025.

## Overcrowding (Objective 3)

A [May 2023 London Assembly answer](https://www.london.gov.uk/who-we-are/what-london-assembly-does/questions-mayor/find-an-answer/overcrowding-london-1), based on ONS Census 2021 TS052, reports **approximately 380,000 London households** with fewer bedrooms than required as of 2021. That London-wide number is now included separately from the GLA's English Housing Survey historical rate. A validated, complete 33-borough TS052 file was not downloaded in this session, so there are **no fabricated borough counts** and no missing-data placeholder box. The relevant ONS table: https://www.ons.gov.uk/datasets/TS052/editions/2021/versions/5.

## Refresh guidance

PAYE, ASHE, MHCLG registration and private rent statistics are revised. Refresh borough data from the original workbooks before claiming consistency with the latest release. All datasets and charts record source and reference dates.
