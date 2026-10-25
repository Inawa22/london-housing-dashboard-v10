"""London housing stock: Objective 1 — total current capacity.

Run: streamlit run app.py
All housing figures come from the bundled official Table 100 ODS extract.
"""
from __future__ import annotations
from pathlib import Path

from boundaries import load_boundaries as load_boundary_data, load_uploaded_geojson
from housing_explainer import render_reference_guide
from tenure_2024 import (CATEGORY_ORDER as TENURE_2024_ORDER, CATEGORY_COLOURS as TENURE_2024_COLOURS,
                         SOURCE_PAGE as TENURE_2024_SOURCE, area_rows as tenure_2024_area_rows,
                         load_local_or_online as load_ons_2024_tenure, read_ons_workbook)

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parent
DATA_FILE = ROOT / 'data' / 'london_dwelling_stock_2012_2025.csv'
GOV_SOURCE = 'https://www.gov.uk/government/statistical-data-sets/live-tables-on-dwelling-stock-including-vacants'
GLA_BOUNDARIES = 'https://data.london.gov.uk/dataset/london-boroughs-e55pw'
REGION_NAME = 'All London'
NAVY = '#17294a'
BLUE = '#2563eb'
TEAL = '#0e9990'
ORANGE = '#e3a35b'
PURPLE = '#8474c7'
TENURE_COLUMNS = {
    'local_authority': 'Local authority',
    'housing_association': 'Housing association',
    'other_public': 'Other public sector',
    'private_sector': 'Private sector',
}
TENURE_COLORS = {'Local authority': BLUE,
                 'Housing association': TEAL,
                 'Other public sector': ORANGE,
                 'Private sector': PURPLE}

st.set_page_config(page_title='London Housing | Stock, Costs, Income & Need',page_icon='🏠', layout='wide',initial_sidebar_state='expanded')
st.markdown('''
<style>
.block-container {max-width: 1380px; padding-top:1.9rem; padding-bottom:3.5rem}
[data-testid="stMetric"] {border:1px solid #e3e9f2;border-radius:13px;padding:16px 18px;background:#fff; min-height:135px}
[data-testid="stMetricLabel"] {font-size:.95rem; color:#556681}
[data-testid="stMetricValue"] {font-weight:730;letter-spacing:-.025em}
.main-intro {color:#596981;font-size:1.04rem;max-width:1000px;line-height:1.65;margin-bottom:.5rem}
.section-kicker {font-size:.75rem;font-weight:800;letter-spacing:.11em;color:#5b70a0}
[data-testid="stSidebar"] {background-color:#f8faff}
.stApp, [data-testid="stAppViewContainer"] {background-color:#f7f9fc}
[data-testid="stVerticalBlockBorderWrapper"] {background-color:#f7f9fc}
</style>''',unsafe_allow_html=True)

@st.cache_data(show_spinner=False)
def load_stock() -> pd.DataFrame:
    df=pd.read_csv(DATA_FILE,dtype={'code':str})
    cols=['local_authority','housing_association','other_public','private_sector','total_dwellings']
    for c in cols: df[c]=pd.to_numeric(df[c],errors='coerce').fillna(0).astype(int)
    df['year']=df['year'].astype(int)
    assert df.groupby('year')['code'].nunique().eq(33).all(), 'Expected 33 local authority areas for each year.'
    return df

@st.cache_data(ttl=86400, show_spinner=False)
def cached_boundaries(expected_codes: tuple[str,...]):
    return load_boundary_data(expected_codes)

def fmt(v):return f'{int(v):,}'
def pct(a,b):return 100*a/b if b else 0.0

def panel_title(number,title,detail):
    st.markdown(f'<div class="section-kicker">VIEW {number}</div>',unsafe_allow_html=True)
    st.subheader(title)
    st.caption(detail)

def ranking_chart(current:pd.DataFrame, selected:str):
    rank=current.sort_values('total_dwellings',ascending=True).copy()
    rank['emphasis'] = ['Selected area' if selected != REGION_NAME and b==selected else 'Other boroughs' for b in rank.borough]
    colors=['#2563eb' if c=='Selected area' else '#94b8e1' for c in rank.emphasis]
    fig=go.Figure(go.Bar(x=rank.total_dwellings,y=rank.borough,orientation='h',marker_color=colors,
                         customdata=rank[['code']].to_numpy(),
                         hovertemplate='<b>%{y}</b><br>%{x:,.0f} dwellings<extra></extra>'))
    fig.update_layout(height=900,margin=dict(l=5,r=15,t=10,b=15),
                      xaxis_title='Existing dwellings',yaxis_title=None,showlegend=False,
                      plot_bgcolor='white',paper_bgcolor='white',font=dict(color=NAVY),
                      xaxis=dict(showgrid=True,gridcolor='#ecf0f5',tickformat=','),
                      yaxis=dict(tickfont=dict(size=11)))
    return fig

def tenure_chart(rows):
    values=[int(rows[col].sum()) for col in TENURE_COLUMNS]
    labels=list(TENURE_COLUMNS.values())
    fig=go.Figure(go.Pie(labels=labels,values=values,hole=.64,sort=False,
         marker_colors=[TENURE_COLORS[x] for x in labels],
         textinfo='percent',textposition='outside',
         hovertemplate='<b>%{label}</b><br>%{value:,.0f} dwellings<br>%{percent}<extra></extra>'))
    fig.update_layout(height=365,margin=dict(l=10,r=10,t=0,b=0),font=dict(color=NAVY),
         paper_bgcolor='white',legend=dict(orientation='h',y=-.10,x=.5,xanchor='center'))
    fig.add_annotation(text=f'<b>{rows.total_dwellings.sum()/1_000_000:.2f}M</b>' if rows.total_dwellings.sum()>1_000_000 else f'<b>{rows.total_dwellings.sum()/1000:.1f}k</b>',
                        x=.5,y=.5,showarrow=False,font=dict(size=24,color=NAVY))
    return fig

@st.cache_data(ttl=24*60*60,show_spinner=False)
def cached_ons_2024_tenure():
    return load_ons_2024_tenure()


def ons_2024_tenure_donut(rows:pd.DataFrame):
    values=[int(rows.loc[rows.tenure.eq(cat),'dwellings'].sum()) for cat in TENURE_2024_ORDER]
    total=sum(values)
    fig=go.Figure(go.Pie(
        labels=TENURE_2024_ORDER,values=values,hole=.64,sort=False,
        marker_colors=TENURE_2024_COLOURS,textinfo='percent',textposition='outside',
        hovertemplate='<b>%{label}</b><br>%{value:,.0f} dwellings<br>%{percent}<extra></extra>'))
    fig.update_layout(height=380,margin=dict(l=20,r=20,t=10,b=30),font=dict(color=NAVY),
        paper_bgcolor='white',legend=dict(orientation='h',y=-.12,x=.5,xanchor='center'))
    fig.add_annotation(text=f'<b>{total/1_000_000:.2f}M</b>' if total>=1_000_000 else f'<b>{total/1000:.1f}k</b>',
                       x=.5,y=.5,showarrow=False,font=dict(size=24,color=NAVY))
    return fig


def render_ons_2024_tenure(selected,stock_current):
    st.markdown('**How many homes are owned or rented? (2024)**')
    st.caption('A closer look at the homes in London: owned outright, owned with a mortgage, '
               'privately rented or socially rented. These are **2024 ONS estimates of dwellings**, '
               'including vacant homes—not 2021 Census household figures.')
    try:
        data=cached_ons_2024_tenure()
    except (ValueError,RuntimeError,ImportError,OSError) as exc:
        st.info('The official 2024 ONS dwelling-tenure file isn’t available yet. '
                'Download the Excel file from ONS and upload it here to see the real figures. '
                'We won’t substitute older Census counts or guessed percentages.')
        st.caption(f'Data loading detail: {exc}')
        upload=st.file_uploader('2024 ONS subnational dwellings-by-tenure workbook (.xlsx)',
                                type='xlsx',key='ons_tenure_2024_upload')
        if upload is None:
            st.link_button('Get the official ONS 2024 Excel file',TENURE_2024_SOURCE)
            return
        try:data=read_ons_workbook(upload.getvalue())
        except ValueError as exc:
            st.error(f'The workbook could not be validated: {exc}')
            st.link_button('Get the official ONS 2024 Excel file',TENURE_2024_SOURCE)
            return
    try:
        focused=tenure_2024_area_rows(data,stock_current,selected)
    except ValueError as exc:
        st.warning(str(exc));return
    left,right=st.columns([1,1.15],gap='large')
    with left:
        st.plotly_chart(ons_2024_tenure_donut(focused),use_container_width=True,
                        config={'displayModeBar':False})
    with right:
        total=int(focused.dwellings.sum())
        st.markdown(f'**{selected if selected != REGION_NAME else "London"} — estimated dwellings by tenure**')
        table=pd.DataFrame([{'Tenure':name,
                             'Dwellings':fmt(focused.loc[focused.tenure.eq(name),'dwellings'].sum()),
                             'Share':f'{pct(focused.loc[focused.tenure.eq(name),"dwellings"].sum(),total):.1f}%'}
                            for name in TENURE_2024_ORDER])
        st.dataframe(table,hide_index=True,use_container_width=True)
        st.caption('The four groups are mutually exclusive within this ONS series. '
                   'It estimates how dwellings are used, rather than which type of organisation provides them.')
    st.caption(f'**Source:** [ONS, subnational estimates of dwellings by tenure, 2024]({TENURE_2024_SOURCE}) '
               '(published 11 February 2026; SPREE small-area estimates). '
               'This measures 2024 stock and must not be added to the 2025 provider-category donut above.')


def tenure_compare_chart(current):
    chart=current.copy()
    for c in TENURE_COLUMNS: chart[c]=100*chart[c]/chart.total_dwellings
    chart=chart.sort_values('borough')
    fig=go.Figure()
    for col,label in TENURE_COLUMNS.items():
        fig.add_bar(y=chart['borough'],x=chart[col],name=label,orientation='h',marker_color=TENURE_COLORS[label],
                    hovertemplate=f'{label}: %{{x:.1f}}%<extra></extra>')
    fig.update_layout(barmode='stack',height=900,margin=dict(l=5,r=5,t=10,b=10),
         xaxis_title='Share of existing stock (%)',yaxis_title='',paper_bgcolor='white',plot_bgcolor='white',
         font=dict(color=NAVY),legend=dict(orientation='h',y=-.07),
         xaxis=dict(range=[0,100],gridcolor='#eff3f8'))
    return fig

def timeline_chart(full, selected, compare):
    if selected == REGION_NAME:
        trend=full.groupby('year',as_index=False).agg(total_dwellings=('total_dwellings','sum'))
        trend['area']='All London'
        extra=full[full.borough.isin(compare)][['year','borough','total_dwellings']].rename(columns={'borough':'area'})
        if not extra.empty:trend=pd.concat([trend,extra],ignore_index=True)
    else:
        trend=full[full.borough.eq(selected)][['year','total_dwellings']].copy()
        trend['area']=selected
        extra=full[(full.borough.isin(compare)) & (~full.borough.eq(selected))][['year','borough','total_dwellings']].rename(columns={'borough':'area'})
        if not extra.empty: trend=pd.concat([trend,extra],ignore_index=True)
    fig=px.line(trend,x='year',y='total_dwellings',color='area',markers=True,
                labels={'year':'Year','total_dwellings':'Number of dwellings','area':'Area'},
                color_discrete_sequence=[BLUE,TEAL,ORANGE,PURPLE])
    fig.update_traces(line_width=3,marker_size=6,hovertemplate='%{x}: %{y:,.0f}<extra>%{fullData.name}</extra>')
    fig.update_layout(height=370,margin=dict(l=5,r=5,t=5,b=10),paper_bgcolor='white',plot_bgcolor='white',
                      font=dict(color=NAVY),xaxis=dict(tickmode='linear',dtick=2,gridcolor='#f1f4f8'),
                      yaxis=dict(tickformat=',',gridcolor='#edf1f6'),legend=dict(orientation='h',y=-.28,x=0))
    return fig

def map_chart(current,geojson,selected):
    data = current.copy()
    all_total = int(data.total_dwellings.sum())
    data['share_of_london'] = data.total_dwellings / all_total * 100
    # Keep links explicit: z value and name always from housing data,
    # polygons keyed by GSS code and checked against all 33 areas.
    custom = data[['borough', 'share_of_london']].to_numpy()
    fig = go.Figure()
    fig.add_trace(go.Choropleth(
        geojson=geojson, locations=data.code, z=data.total_dwellings,
        featureidkey='properties.gss_code', colorscale=[
            [0, '#e8f4fa'], [.2, '#a9d7e8'], [.45, '#63b0d2'], [.7, '#236eae'], [1, '#123a72']
        ], marker_line_color='#ffffff', marker_line_width=0.9,
        colorbar=dict(title=dict(text='Dwellings'), thickness=15, len=0.78,
                      tickformat=',', x=1.01),
        customdata=custom,
        hovertemplate='<b>%{customdata[0]}</b><br>Total dwellings: %{z:,.0f}'
                      '<br>Share of London: %{customdata[1]:.2f}%<extra></extra>',
        name='Dwelling stock',
    ))
    if selected != REGION_NAME:
        highlighted = data[data.borough.eq(selected)]
        if not highlighted.empty:
            fig.add_trace(go.Choropleth(
                geojson=geojson, locations=highlighted.code,
                z=[1], featureidkey='properties.gss_code',
                colorscale=[[0, 'rgba(0,0,0,0)'], [1, 'rgba(0,0,0,0)']],
                showscale=False, marker_line_color='#ec8122', marker_line_width=3.2,
                customdata=highlighted[['borough','total_dwellings']].to_numpy(),
                hovertemplate='<b>%{customdata[0]}</b><br>%{customdata[1]:,.0f} dwellings<extra></extra>',
                name='Selected borough',
            ))
    fig.update_geos(fitbounds='locations', visible=False, projection_type='mercator',
                    bgcolor='#f4f8fc', showland=True, landcolor='#f4f8fc',
                    showocean=True, oceancolor='#f4f8fc', showlakes=False, showcoastlines=False)
    fig.update_layout(height=600, margin=dict(l=0,r=55,t=5,b=0),
                      paper_bgcolor='#f4f8fc', font=dict(color=NAVY),
                      showlegend=False, dragmode=False)
    return fig

def pop_chart(population_data, current, year):
    expected={'borough','population','year'}
    if not expected.issubset(population_data.columns):
        st.error('Population file needs columns: borough, population, year.')
        return
    population_data=population_data.copy()
    population_data['population']=pd.to_numeric(population_data.population,errors='coerce')
    population_data['year']=pd.to_numeric(population_data.year,errors='coerce')
    joined=current.merge(population_data[population_data.year.eq(year)],on='borough',how='inner')
    joined=joined[joined.population.gt(0)]
    if joined.empty:
        st.info(f'No matching borough populations for {year}. Borough names and years must agree.')
        return
    joined['dwellings_per_1000']=1000*joined.total_dwellings/joined.population
    fig=px.bar(joined.sort_values('dwellings_per_1000'),x='dwellings_per_1000',y='borough',orientation='h',
                color_discrete_sequence=[BLUE],labels={'dwellings_per_1000':'Dwellings per 1,000 residents','borough':''})
    fig.update_layout(height=max(320,25*len(joined)),margin=dict(l=5,r=5,t=5,b=5),plot_bgcolor='white')
    st.plotly_chart(fig,use_container_width=True)
    st.caption('Population-adjusted stock is descriptive only; it does not measure housing need, overcrowding or affordability.')

# Objective selector (Objective 1 remains untouched beneath this routing block).
from cost_dashboard import render_cost_dashboard
from unmet_dashboard import render_unmet_dashboard
from housing_assistant import render_assistant
from hypothesis_dashboard import render_hypothesis_dashboard
objective = st.sidebar.radio('Dashboard section',
    ['🔎 · Are we building enough?', '01 · Existing housing stock', '02 · Housing costs & income', '03 · Unmet housing demand', '💬 · Ask the data'],
    index=0, key='objective_section', label_visibility='visible')
st.sidebar.divider()
if objective.startswith('🔎'):
    render_hypothesis_dashboard()
    st.stop()
if objective.startswith('02'):
    render_cost_dashboard()
    st.stop()
if objective.startswith('03'):
    render_unmet_dashboard()
    st.stop()
if objective.startswith('💬'):
    render_assistant()
    st.stop()

stock=load_stock()
years=sorted(stock.year.unique(),reverse=True)
borough_names=sorted(stock.borough.unique())
st.sidebar.markdown('### Explore housing stock')
year=st.sidebar.selectbox('Reference year',years,index=0,help='The baseline year for totals, borough comparisons and tenure.')
selected=st.sidebar.selectbox('Geography',[REGION_NAME]+borough_names,index=0)
comparison=st.sidebar.multiselect('Compare trends with (optional)',[b for b in borough_names if b!=selected],max_selections=3,
           help='Select up to three additional boroughs to compare their housing-stock trends.')
st.sidebar.divider()
st.sidebar.caption('**Definition:** Existing dwelling stock (including vacant homes), not potential future development sites.')
st.sidebar.caption('**Source:** UK government, Table 100. 2022–2025 figures are provisional. 2024 figures revised.')
st.sidebar.link_button('View official source',GOV_SOURCE,use_container_width=True)

current=stock[stock.year.eq(year)].copy()
current=current.sort_values('total_dwellings',ascending=False).reset_index(drop=True)
focused=current if selected==REGION_NAME else current[current.borough.eq(selected)]
focus_name='London' if selected==REGION_NAME else selected
all_total=int(current.total_dwellings.sum())
focus_total=int(focused.total_dwellings.sum())
oldyear=int(stock.year.min())
prior=stock[(stock.year.eq(oldyear)) & ((stock.borough.eq(selected)) if selected!=REGION_NAME else stock.borough.notna())]
prior_total=int(prior.total_dwellings.sum())
change=pct(focus_total-prior_total,prior_total)

st.markdown('<div class="section-kicker">OBJECTIVE 01 · BASELINE SUPPLY</div>',unsafe_allow_html=True)
st.title('London housing capacity')
st.markdown('<p class="main-intro">How many homes already exist across London — and how do they differ by borough, tenure and over time? <b>Here, housing capacity means existing dwelling stock</b>, not homes that could be built in the future.</p>',unsafe_allow_html=True)
st.caption(f'{year} baseline · 32 London boroughs + City of London · Government Table 100')

c1,c2,c3,c4=st.columns(4)
if selected==REGION_NAME:
    with c1:st.metric('Total existing dwellings',fmt(all_total))
    with c2:st.metric('Largest stock',current.iloc[0].borough,help=f'{fmt(current.iloc[0].total_dwellings)} dwellings')
    with c3:st.metric('Smallest stock',current.iloc[-1].borough,help=f'{fmt(current.iloc[-1].total_dwellings)} dwellings')
    with c4:st.metric(f'Change since {oldyear}',f'{change:+.1f}%',delta=f'{focus_total-prior_total:+,} dwellings')
else:
    rank=int(current.index[current.borough.eq(selected)][0])+1
    with c1:st.metric(f'Dwellings in {selected}',fmt(focus_total))
    with c2:st.metric('Share of London stock',f'{pct(focus_total,all_total):.1f}%')
    with c3:st.metric('Borough rank',f'{rank} of 33')
    with c4:st.metric(f'Change since {oldyear}',f'{change:+.1f}%',delta=f'{focus_total-prior_total:+,} dwellings')

st.divider()
panel_title('01','Compare the boroughs','All 33 London local authorities. **Hover over a bar to see the precise number of existing dwellings in that borough.**')
st.plotly_chart(ranking_chart(current,selected),use_container_width=True,config={'displayModeBar':False})

st.divider()
panel_title('02','What kinds of housing make up the stock?',f'Stock composition for {focus_name} in {year}. Hover over each donut segment to see the category, number of dwellings and percentage of the stock.')
left,right=st.columns([1,1.25],gap='large')
with left:
    st.plotly_chart(tenure_chart(focused),use_container_width=True,config={'displayModeBar':False})
    st.caption('**Private sector combines owner-occupied and privately rented homes**; the government table does not separate them. Housing-association and council stock are shown separately.')
with right:
    st.markdown('**Dwellings by provider category**')
    table=pd.DataFrame([{
        'Category':label,
        'Dwellings':fmt(focused[k].sum()),
        'Share of total':f'{pct(focused[k].sum(),focus_total):.1f}%'
    } for k,label in TENURE_COLUMNS.items()])
    st.dataframe(table,hide_index=True,use_container_width=True)
    st.info('Provider category is not the same thing as housing availability, price or an occupied household’s tenure. Council, housing-association and other public stock can be occupied, and the private category contains both owner-occupied and privately rented homes. The shares do not measure how many affordable homes are vacant or accessible.',icon='ℹ️')
with st.expander('Owner-occupied or rented? 2024 ONS dwelling-tenure estimates',expanded=True):
    render_ons_2024_tenure(selected,current)
if selected==REGION_NAME:
    with st.expander('Compare provider-category shares across all boroughs'):
        st.plotly_chart(tenure_compare_chart(current),use_container_width=True,config={'displayModeBar':False})

st.divider()
with st.expander('What types of homes do people live in? (Census 2021 — accommodation type only)'):
    st.caption('This separate, optional Census series describes **2021 housing types** (flats, terraced houses, and so on), not the owner/renter tenure shown in the new 2024 ONS donut. It does not show which types were most purchased or newly rented.')
    typology_path=ROOT/'data'/'borough_accommodation_types_census2021.csv'
    if typology_path.exists():
        ct=pd.read_csv(typology_path)
        selection=ct if selected==REGION_NAME else ct[ct.borough.eq(selected)]
        summary=selection.groupby('property_type',as_index=False)['households'].sum().sort_values('households')
        f=go.Figure(go.Bar(x=summary.households,y=summary.property_type,orientation='h',marker_color=TEAL,
                 hovertemplate='%{y}: %{x:,.0f} households<extra></extra>'))
        f.update_layout(height=325,margin=dict(l=5,r=10,t=10,b=10),paper_bgcolor='white',plot_bgcolor='white',font=dict(color=NAVY),xaxis_title='Households in 2021')
        st.plotly_chart(f,use_container_width=True,config={'displayModeBar':False})
    else:
        st.info('Borough accommodation-type counts have not yet been bundled. The appropriate source is ONS Census 2021 **TS044** (detached, semi-detached, terraced, flats and other types). No type distribution is inferred from average rent or sale prices.')
        st.markdown('[ONS Census 2021 TS044](https://www.ons.gov.uk/datasets/TS044/editions/2021/versions/4)')

st.divider()
panel_title('03','How has housing stock changed?','Compare existing dwellings from 2012 onward. Use the sidebar to select a borough and optional comparators.')
st.plotly_chart(timeline_chart(stock,selected,comparison),use_container_width=True,config={'displayModeBar':False})
st.caption('Historic housing-stock estimates can be revised; year-to-year changes should not be interpreted as net new builds alone.')

st.divider()
panel_title('04','Where is the stock located?',
            'Darker boroughs contain more existing dwellings. These are absolute totals, not density or housing need.')
st.caption('Hover over any borough for its stock and share of London; select a borough in the sidebar to outline it.')
expected_codes=tuple(sorted(current.code.tolist()))
try:
    geo, geometry_origin = cached_boundaries(expected_codes)
    st.plotly_chart(map_chart(current,geo,selected),use_container_width=True,
                    config={'displayModeBar':False})
    st.caption(f'Boundaries: {geometry_origin}. Ordnance Survey Open Data / GLA, Open Government Licence v3.0. '
               f'[Boundary source]({GLA_BOUNDARIES}).')
except Exception as exc:
    st.warning('The public GLA borough boundary service could not be reached, and no cached boundary file is available. '
               'The dwelling-stock figures remain available. To enable the map now, upload a valid borough GeoJSON, '
               'or run `python download_boundaries.py` when internet access is available.')
    with st.expander('Load a London borough GeoJSON / connection details'):
        uploaded_geometry=st.file_uploader('London borough boundary GeoJSON',type=['geojson','json'])
        if uploaded_geometry is not None:
            try:
                geo=load_uploaded_geojson(uploaded_geometry.read(),expected_codes)
                st.plotly_chart(map_chart(current,geo,selected),use_container_width=True,
                                config={'displayModeBar':False})
                st.success('All 33 London local authority boundaries matched to housing-stock data.')
            except (ValueError, TypeError, UnicodeDecodeError) as upload_error:
                st.error(f'Could not use the uploaded geometry: {upload_error}')
        st.caption('Expected: a GeoJSON FeatureCollection with 33 Polygon/MultiPolygon features '
                   'and a `gss_code` property matching the stock dataset. '
                   f'[Official boundary information]({GLA_BOUNDARIES}).')
        st.code(str(exc)[:700], language=None)

with st.expander('About dwellings per 1,000 residents'):
    population_file=ROOT/'data'/'borough_population_2021.csv'
    if population_file.exists() and year==2021:
        pop_chart(pd.read_csv(population_file),current,year)
        st.caption('Population source: ONS Census 2021 TS001. Stock numerator: 2021 government Table 100. This is dwelling stock relative to residents, not a vacancy, household-size or housing-need indicator.')
    else:
        st.markdown('To compare dwellings relative to local population, we would need **borough-level population estimates from the same reference year** as the dwelling stock. Table 100 contains dwelling counts only; dividing by homelessness-household counts would be the wrong denominator.')
    st.markdown('That rate is intentionally **not estimated** until a compatible ONS population series has been checked and bundled. [ONS population estimates](https://www.ons.gov.uk/peoplepopulationandcommunity/populationandmigration/populationestimates).')

with st.expander('Methodology and limitations'):
    st.markdown(f'''- **Current housing capacity = existing dwelling stock** for this project, including occupied and vacant homes.
- **Coverage:** 32 London boroughs and the City of London (33 local authority areas).
- **Official categories:** local authority, housing association/private registered provider, other public sector, private sector.
- **Private sector:** includes both owner-occupied and privately rented homes, which cannot be separated using this source alone.
- **Time:** 2012–2025 available in this curated extract. Figures from 2022 onward are provisional and 2024 has been revised.
- **Limits:** this stock measure cannot determine affordability, housing availability, overcrowding, vacancy, or unmet demand on its own.
- [**Source: government Table 100**]({GOV_SOURCE}).''')


render_reference_guide()
