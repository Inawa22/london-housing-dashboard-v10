"""Objective 3 — descriptive measures of recorded homelessness and wider housing need.
Do not add distinct datasets together; people, households, quarterly flows and
period-end stocks are different measures. Missing borough returns stay NA.
"""
from __future__ import annotations
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st
from boundaries import load_boundaries
from housing_explainer import render_reference_guide

HERE=Path(__file__).resolve().parent
DATA=HERE/'data'
LONDON='E12000007'
GOV='https://www.gov.uk/government/collections/homelessness-statistics'
CHAIN='https://data.london.gov.uk/dataset/chain-reports'
WAITING='https://www.gov.uk/government/statistical-data-sets/live-tables-on-rents-lettings-and-tenancies'
CENSUS='https://www.ons.gov.uk/datasets/TS052/editions/2021/versions/5'
NAVY='#17294a';BLUE='#2563eb';TEAL='#0e9990';ORANGE='#e3a35b';LIGHT='#9fc6e4'

@st.cache_data(show_spinner=False)
def source_data():
    statutory=pd.read_csv(DATA/'statutory_homelessness_2025.csv',dtype={'code':'string'})
    reasons=pd.read_csv(DATA/'homelessness_reasons_2025.csv',dtype={'code':'string'})
    chain=pd.read_csv(DATA/'chain_rough_sleeping.csv',dtype={'code':'string'})
    for df in (statutory,reasons,chain):
        df['code']=df['code'].str.upper().str.strip()
    assert statutory.groupby('period')['code'].nunique().eq(34).all(), 'Expected 33 boroughs + London each quarter'
    assert chain.groupby('period')['code'].nunique().eq(34).all(), 'Expected 33 boroughs + London each CHAIN quarter'
    return statutory,reasons,chain

@st.cache_data(show_spinner=False)
def census_context():
    return pd.read_csv(DATA/'london_overcrowding_ehs_gla.csv')

@st.cache_data(ttl=86400,show_spinner=False)
def boundaries(codes):return load_boundaries(codes)

def pretty(x):
    if pd.isna(x):return 'Not available'
    return f'{int(round(x)):,}'

def ratefmt(x):
    return 'Not available' if pd.isna(x) else f'{x:.1f}'

def subtitle(n,title,detail):
    st.markdown(f'<div class="section-kicker">VIEW {n}</div>',unsafe_allow_html=True)
    st.subheader(title)
    st.caption(detail)

def bar_ranking(frame,field,selected,unit):
    chart=frame.dropna(subset=[field]).sort_values(field,ascending=True)
    fig=go.Figure(go.Bar(y=chart['borough'],x=chart[field],orientation='h',
        marker_color=[BLUE if c==selected else LIGHT for c in chart['code']],
        hovertemplate=f'<b>%{{y}}</b><br>%{{x:,.1f}} {unit}<extra></extra>'))
    fig.update_layout(height=max(420,len(chart)*27),margin=dict(t=12,l=5,b=25,r=15),
        paper_bgcolor='white',plot_bgcolor='white',font=dict(color=NAVY),
        xaxis_title=unit,yaxis_title='',xaxis=dict(gridcolor='#eff3f8'))
    return fig

def trend_chart(frame,field,selected,title,unit,periods):
    fig=go.Figure()
    if selected!=LONDON:
        borough=frame[frame.code.eq(selected)].set_index('period').reindex(periods)
        fig.add_scatter(x=periods,y=borough[field],mode='lines+markers',name='Selected borough',
            line=dict(color=BLUE,width=3),connectgaps=False,
            hovertemplate='%{x}: %{y:,.0f}<extra>Selected borough</extra>')
    london=frame[frame.code.eq(LONDON)].set_index('period').reindex(periods)
    fig.add_scatter(x=periods,y=london[field],mode='lines+markers',
        name='London (published series)',line=dict(color=TEAL,width=3,dash='dash' if selected!=LONDON else 'solid'),
        connectgaps=False,hovertemplate='%{x}: %{y:,.0f}<extra>London</extra>')
    fig.update_layout(title=dict(text=title,font=dict(size=15)),height=310,
        margin=dict(t=45,l=10,r=15,b=15),paper_bgcolor='white',plot_bgcolor='white',font=dict(color=NAVY),
        yaxis_title=unit,yaxis=dict(gridcolor='#eff3f8',rangemode='tozero'),
        xaxis_title='',legend=dict(orientation='h',y=-.25))
    return fig

def fill_map(frame,field,selected,label,codes):
    geo,src=boundaries(codes)
    mapped=frame[['code','borough',field]].copy().dropna(subset=[field])
    if mapped.empty:return None,src
    fig=go.Figure(go.Choropleth(
        geojson=geo,locations=mapped['code'],z=mapped[field],featureidkey='properties.gss_code',
        colorscale=[[0,'#e7f4fa'],[.3,'#a2d3e7'],[.65,'#4d98c7'],[1,'#163e77']],
        marker_line_color='white',marker_line_width=.8,
        customdata=mapped[['borough']].to_numpy(),
        colorbar=dict(title=label,len=.7,thickness=15),
        hovertemplate='<b>%{customdata[0]}</b><br>%{z:,.1f}<extra></extra>'))
    if selected!=LONDON and selected in set(mapped.code):
        highlight=mapped[mapped.code.eq(selected)]
        fig.add_trace(go.Choropleth(geojson=geo,locations=highlight.code,z=[1],
            featureidkey='properties.gss_code',colorscale=[[0,'rgba(0,0,0,0)'],[1,'rgba(0,0,0,0)']],
            showscale=False,marker_line_color='#e48132',marker_line_width=3,
            hoverinfo='skip'))
    fig.update_geos(fitbounds='locations',visible=False,bgcolor='#f4f8fc',projection_type='mercator',
        showland=True,landcolor='#f4f8fc',showocean=True,oceancolor='#f4f8fc',showlakes=False,showcoastlines=False)
    fig.update_layout(height=560,margin=dict(t=5,b=5,l=5,r=30),paper_bgcolor='#f4f8fc')
    return fig,src

def optionally_wider_data():
    # Curated, borough-level CSV uploads are optional and never synthesized from other indicators.
    # A user can create a file from the directly linked official source when those data are available.
    path=DATA/'borough_waiting_lists.csv'
    if path.exists():
        df=pd.read_csv(path,dtype={'code':'string'})
        if {'code','year','waiting_households'}.issubset(df.columns):return df
    return None

def optionally_census_data():
    path=DATA/'borough_overcrowding_census2021.csv'
    if path.exists():
        df=pd.read_csv(path,dtype={'code':'string'})
        if {'code','overcrowded_households','total_households'}.issubset(df.columns):return df
    return None

def render_unmet_dashboard():
    data,reasons,chain=source_data()
    names=data[(data.period=='2025 Q4') & data.level.eq('Borough')][['code','borough']].sort_values('borough')
    options={LONDON:'All London',**dict(zip(names.code,names.borough))}
    st.sidebar.markdown('### Explore unmet housing need')
    selected=st.sidebar.selectbox('Area',['All London']+names.borough.tolist(),key='unmet_geography')
    code=LONDON if selected=='All London' else next(c for c,n in options.items() if n==selected)
    st.sidebar.caption('Official London regional figures are used as published; missing borough returns are not replaced with zero.')
    st.sidebar.link_button('Statutory homelessness sources',GOV,use_container_width=True)
    st.sidebar.link_button('CHAIN source',CHAIN,use_container_width=True)

    st.markdown('<div class="section-kicker">OBJECTIVE 03 · RECORDED HOUSING NEED</div>',unsafe_allow_html=True)
    st.title('Unmet housing demand')
    st.markdown('<p class="main-intro">Explore recorded homelessness, households in temporary accommodation, people seen rough sleeping, and wider housing need. These indicators describe different groups and cannot be added to produce a single total.</p>',unsafe_allow_html=True)
    home,rough,wider=st.tabs(['Homelessness & temporary accommodation','Rough sleeping','Wider housing need'])
    codes=tuple(sorted(names.code.tolist()))
    with home:
        quarter=st.selectbox('Reference quarter',['2025 Q4','2025 Q3','2025 Q2','2025 Q1'],key='homeless_quarter')
        current=data[data.period.eq(quarter)]
        area=current[current.code.eq(code)].iloc[0]
        date={'2025 Q4':'31 December 2025','2025 Q3':'30 September 2025','2025 Q2':'30 June 2025','2025 Q1':'31 March 2025'}[quarter]
        st.caption(f'Assessments: during {quarter} · Temporary accommodation: snapshot at {date} · Units shown individually.')
        a,b,c,d=st.columns(4)
        a.metric('Households owed a duty',pretty(area.owed_duty),help='Total households assessed as owed a prevention or relief duty during the quarter (A1).')
        b.metric('Households in temporary accommodation',pretty(area.ta_households),help='Households in temporary accommodation at the quarter end (TA1).')
        c.metric('Children in temporary accommodation',pretty(area.ta_children),help='Individual children in temporary accommodation at the quarter end (TA1).')
        d.metric('TA households per 1,000 households',ratefmt(area.ta_rate_1000),help='Published rate from MHCLG TA1; denominator: area household estimate, not number of dwellings.')
        st.caption('**Source:** MHCLG statutory homelessness local authority tables A1 and TA1. An unavailable borough return is not a zero. The published London totals can include adjustments for missing local reports.')
        st.divider()
        subtitle('01','Where is temporary accommodation most widely used?',
            '“Burden” means either the total number of households in temporary accommodation or that number relative to the local household population. Use rates per 1,000 to compare differently sized boroughs. Hover over bars for the exact values; missing returns are omitted.')
        mode=st.radio('Comparison measure',['Number of households','Households per 1,000 households'],horizontal=True,key='ta_metric')
        field='ta_households' if mode.startswith('Number') else 'ta_rate_1000'
        london_row=current[current.code.eq(LONDON)].iloc[0]
        st.caption(f'London-wide published reference: **{pretty(london_row.ta_households)} households** · **{ratefmt(london_row.ta_rate_1000)} per 1,000 households**.')
        boroughs=current[current.level.eq('Borough')]
        excluded=boroughs[boroughs[field].isna()]
        if not excluded.empty:
            st.warning('No published value for: '+', '.join(excluded.borough.tolist())+'. Not plotted.')
        st.plotly_chart(bar_ranking(boroughs,field,code,'households' if field=='ta_households' else 'households per 1,000 households'),use_container_width=True)
        st.divider()
        subtitle('02','Prevention and relief duties','A prevention duty concerns threatened homelessness; a relief duty concerns households already homeless. Both are quarterly household counts.')
        grouped=pd.DataFrame({'Duty':['Prevention','Relief'],'Households':[area.prevention,area.relief]})
        f=px.bar(grouped,x='Duty',y='Households',color='Duty',text='Households',color_discrete_map={'Prevention':TEAL,'Relief':BLUE})
        f.update_traces(texttemplate='%{text:,.0f}',textposition='outside')
        f.update_layout(showlegend=False,height=330,margin=dict(t=20,b=10,l=5,r=5),plot_bgcolor='white',paper_bgcolor='white',font=dict(color=NAVY),yaxis=dict(rangemode='tozero'))
        st.plotly_chart(f,use_container_width=True)
        st.divider()
        subtitle('03','How has recorded homelessness changed?','Four quarters are available for 2025. Lines show two different indicators; missing borough data remain gaps.')
        periods=['2025 Q1','2025 Q2','2025 Q3','2025 Q4']
        lc,rc=st.columns(2)
        with lc:st.plotly_chart(trend_chart(data,'ta_households',code,'Households in temporary accommodation','Households',periods),use_container_width=True)
        with rc:st.plotly_chart(trend_chart(data,'owed_duty',code,'Households owed prevention or relief duty','Households',periods),use_container_width=True)
        st.divider()
        subtitle('04','Why are households becoming homeless?','Reported reason for loss of last settled home or its threatened loss; based on A2P/A2R.')
        duty=st.radio('Duty type',['Prevention','Relief'],horizontal=True,key='reasons_duty')
        rdata=reasons[(reasons.period.eq(quarter)) & (reasons.code.eq(code)) & (reasons.duty.eq(duty))].dropna(subset=['households'])
        rdata=rdata.sort_values('households',ascending=False).head(9).sort_values('households')
        rr=go.Figure(go.Bar(y=rdata['reason'],x=rdata['households'],orientation='h',marker_color=TEAL if duty=='Prevention' else BLUE,
            hovertemplate='%{y}<br>%{x:,.0f} households<extra></extra>'))
        rr.update_layout(height=430,margin=dict(l=5,r=10,t=10,b=15),plot_bgcolor='white',paper_bgcolor='white',font=dict(color=NAVY),xaxis_title='Households')
        st.plotly_chart(rr,use_container_width=True)
        st.caption('Because MHCLG rounds published estimates, the listed categories may not sum exactly to the published total.')
        with st.expander('Types of temporary accommodation'):
            types={
                'Bed and breakfast':area.ta_bed_breakfast,
                'Nightly paid private':area.ta_nightly_private,
                'Hostel / refuge':area.ta_hostel_refuge,
                'Private sector leased':area.ta_private_leased,
                'Council / housing association':area.ta_social_stock,
                'Other / not known':area.ta_other,
            }
            df=pd.DataFrame([{'Type':k,'Households':v} for k,v in types.items()]).dropna(subset=['Households'])
            if df.empty:st.info('No published accommodation-type breakdown for this area and quarter.')
            else:
                fi=px.bar(df.sort_values('Households'),x='Households',y='Type',orientation='h',color_discrete_sequence=[BLUE]);fi.update_layout(height=320)
                st.plotly_chart(fi,use_container_width=True)
            st.caption('Source: MHCLG Table TA1. Category counts may differ slightly from total due to rounding.')
        st.divider()
        subtitle('05','Map — temporary accommodation by borough','Darker shades represent more households in temporary accommodation, or a greater rate per 1,000 households, depending on the selected comparison measure.')
        try:
            mf,src=fill_map(boroughs,field,code, 'TA households' if field=='ta_households' else 'Per 1,000',codes)
            if mf is not None:st.plotly_chart(mf,use_container_width=True,config={'displayModeBar':False})
            st.caption(f'Boundaries: {src}. Missing values are not treated as zero.')
        except Exception:
            st.info('The map needs verified GLA borough polygons. Place the official `london_boroughs.geojson` in the project’s `data/` folder (or run `python download_boundaries.py` while online). The chart above remains fully available. No approximate borough shapes are generated.')
        st.markdown('**Underhoused households (overcrowding)**')
        st.caption('Some households have housing but fewer bedrooms than the official standard requires. The current files include a London-wide historical survey indicator (see the Wider housing need tab), but not a verified borough count, so this measure is not shown here as an invented statistic.')

    with rough:
        chain_periods=['2024-25 Q2','2024-25 Q3','2024-25 Q4','2025-26 Q1','2025-26 Q2','2025-26 Q3','2025-26 Q4','2026-27 Q1']
        cq=st.selectbox('CHAIN reporting quarter',chain_periods,index=len(chain_periods)-1,key='chain_quarter')
        cnow=chain[chain.period.eq(cq)]; crow=cnow[cnow.code.eq(code)].iloc[0]
        st.metric('People seen sleeping rough',pretty(crow.people_seen))
        st.caption(f'{cq} · CHAIN P1 · **individual people seen during the quarter**, not households or a single-night census. Someone may appear in more than one borough across a reporting period; borough totals must not be summed to produce the London estimate.')
        subtitle('01','Rough sleeping by area','Reported people seen during the selected reporting quarter.')
        st.plotly_chart(bar_ranking(cnow[cnow.level.eq('Borough')],'people_seen',code,'people seen rough sleeping'),use_container_width=True)
        subtitle('02','Rough sleeping over time','Published CHAIN quarterly counts, London and selected borough.')
        st.plotly_chart(trend_chart(chain,'people_seen',code,'Quarterly rough sleeping: people seen','People',chain_periods),use_container_width=True)
        st.divider()
        subtitle('03','Map — people seen rough sleeping','Outreach-observed people seen rough sleeping, rather than households.')
        try:
            rmap,src=fill_map(cnow[cnow.level.eq('Borough')],'people_seen',code,'People',codes)
            if rmap is not None:st.plotly_chart(rmap,use_container_width=True,config={'displayModeBar':False})
            st.caption(f'Boundaries: {src}. Borough counts should not be summed as distinct people.')
        except Exception:
            st.info('The map needs verified official GLA borough polygons. Run `python download_boundaries.py` when online. Borough rankings remain available without the map.')

    with wider:
        st.markdown('### Other indicators of housing need')
        st.info('Some households have a home but still lack enough space. Housing-need measures can overlap, so we cannot simply add their totals together.')
        p1,p2=st.columns(2)
        with p1:
            st.metric('London housing-register entries · March 2025','341,421 households')
            st.caption('[London Assembly, March 2026](https://www.london.gov.uk/sites/default/files/2026-03/Housing%20Committee%20-%20Allocations%20in%20social%20housing%20report%20-%20FINAL.pdf). Administrative register count, **not** a count of unique households currently needing housing.')
        with p2:
            st.metric('London households with too few bedrooms · Census 2021','About 380,000')
            st.caption('[Mayor of London, based on ONS Census TS052](https://www.london.gov.uk/who-we-are/what-london-assembly-does/questions-mayor/find-an-answer/overcrowding-london-1). This is a **2021 census** estimate, not a 2025 count.')
        wait=optionally_wider_data(); census=optionally_census_data()
        if wait is not None:
            wait['year']=pd.to_numeric(wait.year,errors='coerce');wait['waiting_households']=pd.to_numeric(wait.waiting_households,errors='coerce')
            wlatest=wait[wait.year.eq(wait.year.max())].merge(names,on='code',how='inner')
            st.subheader(f'Households on housing registers — {int(wait.year.max())}')
            st.plotly_chart(bar_ranking(wlatest,'waiting_households',code,'registered households'),use_container_width=True)
            st.caption('Source: [London Assembly Affordable Housing Monitor 2025, p.26](https://www.london.gov.uk/sites/default/files/2025-07/Affordable%20Housing%20Monitor%202025_1.pdf), reporting MHCLG Table 600 March 2024. Borough values are transcribed from the official map. The separately published 2024 London total is **336,357**, while printed borough labels add to **336,366** (nine higher); the dashboard keeps the official regional figure rather than replacing it with a summed total. Borough registers can differ in eligibility and maintenance, and households may appear on multiple lists.')
            st.divider()
        if census is not None:
            census['overcrowded_households']=pd.to_numeric(census.overcrowded_households,errors='coerce')
            census['total_households']=pd.to_numeric(census.total_households,errors='coerce')
            census=census.merge(names,on='code',how='inner');census=census[census.total_households.gt(0)].copy()
            census['share_pct']=100*census.overcrowded_households/census.total_households
            st.subheader('Overcrowded households — 2021 Census')
            st.plotly_chart(bar_ranking(census,'share_pct',code,'% overcrowded households'),use_container_width=True)
        st.divider()
        st.markdown('**London-wide overcrowding — historical context**')
        context=census_context()
        available_years=sorted(context.year.unique());ymax=max(available_years)
        latest=context[(context.tenure.eq('All tenures')) & context.year.eq(ymax)]
        if not latest.empty:
            st.metric(f'London overcrowding rate · {ymax}–{str(ymax+1)[-2:]}',f'{latest.iloc[0].overcrowding_pct:.1f}%')
        available=context[context.tenure.eq('All tenures')].sort_values('year')
        fig=px.line(available,x='year',y='overcrowding_pct',markers=False,color_discrete_sequence=[BLUE])
        fig.update_layout(height=280,paper_bgcolor='white',plot_bgcolor='white',font=dict(color=NAVY),yaxis_title='Households overcrowded (%)',xaxis_title='Start of reporting year')
        st.plotly_chart(fig,use_container_width=True)
        st.caption('Regional (London-wide) EHS three-year rolling estimate reported in GLA Housing in London 2025, figure 4.9. It is **not** a borough-level measure and must not be substituted for 2021 Census borough rates.')

    with st.expander('About these measures and their sources'):
        st.markdown(f'''**Statutory homelessness:** MHCLG detailed local authority tables, 2025 quarters. A1 counts households newly assessed as owed a prevention/relief duty during each quarter. TA1 counts households placed in temporary accommodation at the quarter end, plus individual children. Rates per 1,000 households are published in Table TA1. Figures may be rounded; some borough returns are missing; London regional totals can include adjustments. [Official source]({GOV}).

**Rough sleeping:** CHAIN quarterly table P1 records people seen sleeping rough by outreach services. Individuals seen across different boroughs must not be summed as unique people. [Source]({CHAIN}).

**Waiting lists:** The 2024 borough chart comes from the MHCLG Table 600 map in the London Assembly's 2025 Affordable Housing Monitor; the 2025 London total is cited separately from a 2026 London Assembly report. These are registration counts, not an annual flow of housing applications or a unique count of unmet demand.

**2021 Census overcrowding:** The Mayor's published answer cites approximately 380,000 London households with too few bedrooms (2021). This is different from the English Housing Survey overcrowding time series below.

**Overcrowding (regional context):** GLA Housing in London 2025 figure 4.9, based on the English Housing Survey. The regional rate is not equivalent to a borough rate. [GLA housing data](https://data.london.gov.uk/).

**Important:** The dashboard does not infer total unmet demand by adding waiting lists, temporary accommodation, duty assessments, overcrowding and rough-sleeping figures because units, dates, definitions and memberships overlap.''')
    render_reference_guide()
