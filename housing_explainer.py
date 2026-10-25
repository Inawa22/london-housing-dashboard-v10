"""Human-readable definitions, vetted source descriptions and publication caveats."""
from __future__ import annotations
import streamlit as st

SOURCE_TABLE = [
    ('Housing stock / provider categories', 'MHCLG Table 100', 'Administrative statistical return compiled by central government; borough-by-year counts, subject to revision.', 'https://www.gov.uk/government/statistical-data-sets/live-tables-on-dwelling-stock-including-vacants'),
    ('Private monthly rents', 'ONS Price Index of Private Rents', 'Official modelled prices from administrative tenancy evidence; borough and independently published regional estimates.', 'https://www.ons.gov.uk/economy/inflationandpriceindices/datasets/priceindexofprivaterentsukmonthlypricestatistics'),
    ('Purchase prices and sales volume', 'HM Land Registry / UK House Price Index', 'Official statistical model based on registered residential transactions; recent data can be revised.', 'https://www.gov.uk/government/collections/uk-house-price-index-reports'),
    ('Homelessness & temporary accommodation', 'MHCLG statutory homelessness tables', 'Official local-authority statutory returns: duty assessments and quarter-end temporary accommodation.', 'https://www.gov.uk/government/collections/homelessness-statistics'),
    ('People seen rough sleeping', 'CHAIN', 'Outreach-service recording of individuals seen sleeping rough, rather than a household survey or census.', 'https://data.london.gov.uk/dataset/chain-reports'),
    ('London-wide overcrowding trend', 'GLA Housing in London / English Housing Survey', 'Regional survey-based estimates; not suitable for assigning a borough rate.', 'https://data.london.gov.uk/'),
    ('Occupied-household tenure (2021)', 'ONS Census 2021, TS054', 'Population census of household tenure; not interchangeable with 2025 dwelling-stock provider sectors.', 'https://www.ons.gov.uk/datasets/TS054/editions/2021/versions/5'),
    ('Borough polygons', 'Greater London Authority / Ordnance Survey Open Data', 'Official boundary geometry and nine-character GSS identifiers; geometry is not statistical housing data.', 'https://data.london.gov.uk/dataset/london-boroughs-e55pw'),
]

DEFINITIONS = {
    'Housing capacity (in this dashboard)': 'The existing stock of self-contained dwellings, including vacant ones; NOT buildable land, approved developments or future construction capacity.',
    'Dwelling': 'A unit of accommodation that may be occupied or vacant. It does not necessarily equal one household, one person, an available home or a home that is affordable.',
    'Dwelling stock': 'Number of existing dwellings at a given point in time, including occupied and unoccupied units. This is the baseline in Objective 1.',
    'Stock provider category': 'Who owns or provides the homes for the administrative statistics: local authority, private registered provider/housing association, other public sector, and private sector. These are not household tenure categories.',
    'Private sector (Table 100)': 'A residual owner/provider category including both owner-occupied and privately rented dwellings. A high share DOES NOT establish how many people rent, or that all such housing is high-priced.',
    'Tenure (ONS Census)': 'How a household occupies a home—owned outright/mortgaged, shared ownership, social rented, privately rented, or lives rent-free. Census tenure describes occupied households, not all dwellings.',
    'London benchmark': 'An independently published London regional price or rent estimate used as a comparator; it is not a simple mean of the 32/33 borough values.',
    'Prevention duty': 'A local authority duty to help an eligible applicant who is threatened with homelessness; measured in households owed assistance over a reporting period.',
    'Relief duty': 'A local authority duty to help an eligible applicant who is already homeless to secure accommodation; measured in households owed assistance over a reporting period.',
    'Temporary accommodation (TA)': 'Interim housing arranged by local authorities for households owed certain homelessness duties. TA is not necessarily permanent, affordable or an available home.',
    'Temporary-accommodation burden': 'How many households are in TA in a borough, or how large that count is relative to the number of households normally living there. A rate per 1,000 helps compare differently sized areas.',
    'Rough sleeping (CHAIN)': 'People observed sleeping rough by outreach services during a reporting quarter. These are individuals, not households, and people may be seen in multiple boroughs.',
    'Overcrowding / underhousing': 'A household has fewer bedrooms than it needs under the official bedroom standard (occupancy rating −1 or below). It is not the same as being homeless.',
    'Borough boundaries': 'Geographic polygons used to colour local authorities on the maps. OGL-licensed GLA/Ordnance Survey boundaries are matched to the data by GSS code.',
}


def render_reference_guide():
    with st.expander('Definitions and data-source reliability', expanded=False):
        st.markdown('**Key terms**')
        for term, definition in DEFINITIONS.items():
            st.markdown(f'**{term}:** {definition}')
        st.markdown('**Where the data come from**')
        for metric, publisher, why, url in SOURCE_TABLE:
            st.markdown(f'**{metric} — [{publisher}]({url})**  \n{why}')
        st.caption('Official status does not guarantee that every return is complete or directly comparable: check dates, geographic coverage, missing values and methodology before drawing conclusions.')
