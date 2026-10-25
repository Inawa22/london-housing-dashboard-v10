"""Objective 2: descriptive purchase-price and private-rental dashboards.

Sources bundled as extracted monthly CSVs from the user's official HPI and
ONS Price Index of Private Rents XLSX workbooks. All comparisons are made
at a matched date and geographical level; never average borough headline
prices to reproduce London's independently published regional estimates.
"""
from __future__ import annotations

from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from boundaries import load_boundaries, load_uploaded_geojson
from housing_explainer import render_reference_guide

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / 'data'
LONDON_CODE = 'E12000007'
CITY_CODE = 'E09000001'
LONDON_LABEL = 'All London'
NAVY = '#17294a'
BLUE = '#2563eb'
TEAL = '#0e9990'
ORANGE = '#d98136'
MUTED = '#aec5df'
RENT_SOURCE = 'https://www.ons.gov.uk/economy/inflationandpriceindices/datasets/priceindexofprivaterentsukmonthlypricestatistics'
PRICE_SOURCE = 'https://www.gov.uk/government/collections/uk-house-price-index-reports'
BOUNDARY_SOURCE = 'https://data.london.gov.uk/dataset/london-boroughs-e55pw'


@st.cache_data(show_spinner=False)
def load_cost_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    price = pd.read_csv(DATA_DIR / 'house_prices.csv', dtype={'code':str}, parse_dates=['date'])
    rent = pd.read_csv(DATA_DIR / 'private_rents.csv', dtype={'code':str}, parse_dates=['date'])
    stock = pd.read_csv(DATA_DIR / 'london_dwelling_stock_2012_2025.csv', dtype={'code':str}, usecols=['borough','code'])
    canonical = stock.drop_duplicates('code').set_index('code')['borough'].to_dict()
    # Canonical display labels across both workbooks; authoritative matching is via GSS codes.
    for frame in (price, rent):
        frame['borough'] = frame.apply(lambda row: ('London' if row.code == LONDON_CODE else canonical.get(row.code,row.borough)),axis=1)
        frame.sort_values(['date','code'],inplace=True)
        assert not frame.duplicated(['date','code']).any(), 'Duplicate geography-month in costs dataset'
        assert frame.loc[frame.code.ne(LONDON_CODE),'code'].str.startswith('E09').all()
    assert price.loc[price.code.str.startswith('E09'),'code'].nunique()==33
    assert rent.loc[rent.code.str.startswith('E09'),'code'].nunique()==32
    assert CITY_CODE not in set(rent.code)
    return price,rent


@st.cache_data(ttl=86400, show_spinner=False)
def costs_boundaries(expected_codes: tuple[str,...]):
    # Cache failures as well as successes so two Streamlit tabs never make
    # repeated slow network requests when working offline.
    try:
        geo, origin = load_boundaries(expected_codes)
        return geo, origin, None
    except Exception as exc:
        return None, None, str(exc)


def fmt_month(x):
    return pd.Timestamp(x).strftime('%B %Y')


def get_latest(df, date):
    return df.loc[df.date.eq(pd.Timestamp(date))].copy()


def annual_price_change(df:pd.DataFrame, code:str, date, field:str) -> float | None:
    """YoY percentage: same calendar month one year previously (not month-on-month)."""
    date=pd.Timestamp(date)
    x=df.loc[(df.code==code)&(df.date==date),field]
    old=df.loc[(df.code==code)&(df.date==date-pd.DateOffset(years=1)),field]
    if x.empty or old.empty or pd.isna(old.iloc[0]) or old.iloc[0]<=0:
        return None
    return float((x.iloc[0]/old.iloc[0]-1)*100)


def comparison_row(frame, code, field):
    row=frame.loc[frame.code.eq(code)]
    if row.empty or pd.isna(row.iloc[0][field]):return None
    return row.iloc[0]


def bar_ranking(current, field, selected, london_value, mode):
    boroughs=current[current.code.str.startswith('E09')].dropna(subset=[field]).sort_values(field,ascending=True).copy()
    colors=[BLUE if c==selected and selected!=LONDON_CODE else ('#5a92c7' if i >=len(boroughs)-3 else MUTED)
            for i,c in enumerate(boroughs.code)]
    fig=go.Figure(go.Bar(
        x=boroughs[field], y=boroughs.borough, orientation='h', marker_color=colors,
        hovertemplate='<b>%{y}</b><br>£%{x:,.0f}'+('/month' if mode=='rent' else '')+'<extra></extra>',
        text=['£'+f'{v:,.0f}' for v in boroughs[field]],textposition='outside',
        textfont=dict(size=10,color=NAVY),cliponaxis=False,
    ))
    if london_value is not None:
        fig.add_vline(x=float(london_value),line_dash='dash',line_color=ORANGE,line_width=1.8)
    max_val=float(boroughs[field].max())
    fig.update_layout(height=max(730,24*len(boroughs)+105),margin=dict(l=5,r=55,t=42,b=24),
                      xaxis_title='Average monthly rent (£)' if mode=='rent' else 'Average property price (£)',
                      yaxis_title=None,showlegend=False,font=dict(color=NAVY),
                      paper_bgcolor='white',plot_bgcolor='white',
                      xaxis=dict(gridcolor='#eef2f8',tickprefix='£',tickformat=',',range=[0,max_val*1.20]),
                      yaxis=dict(tickfont=dict(size=11)))
    return fig


def trend_chart(data, field, selected, extras, period):
    last=data.date.max()
    years={'Last 3 years':3,'Last 5 years':5,'Last 10 years':10,'All available':None}[period]
    if years is not None:
        data=data.loc[data.date.ge(last-pd.DateOffset(years=years))]
    codes=[LONDON_CODE]
    if selected!=LONDON_CODE:codes.append(selected)
    codes += [c for c in extras if c not in codes]
    colors=[ORANGE, BLUE, TEAL, '#8d75c9']
    fig=go.Figure()
    for ix,code in enumerate(codes):
        s=data.loc[data.code.eq(code)].sort_values('date')
        if s.empty or not s[field].notna().any():continue
        label='London benchmark' if code==LONDON_CODE else s.borough.iloc[0]
        fig.add_trace(go.Scatter(x=s.date,y=s[field],mode='lines',name=label,
            line=dict(color=colors[ix % len(colors)],width=3 if code==selected else 2.3,
                      dash='dash' if code==LONDON_CODE and selected!=LONDON_CODE else 'solid'),
            hovertemplate='%{x|%b %Y}: £%{y:,.0f}<extra>'+label+'</extra>'))
    fig.update_layout(height=385,margin=dict(l=8,r=10,t=15,b=16),paper_bgcolor='white',plot_bgcolor='white',
        font=dict(color=NAVY),xaxis=dict(title=None,gridcolor='#f0f3f8'),
        yaxis=dict(title='Average monthly rent (£)' if field=='rent_gbp' else 'Average property price (£)',
                   tickprefix='£',tickformat=',',gridcolor='#eef2f8'),
        legend=dict(orientation='h',y=-.25,x=0),hovermode='x unified')
    return fig


def breakdown_chart(row, kind='bedroom'):
    if kind=='bedroom':
        columns=[('One bedroom','rent_1bed_gbp'),('Two bedrooms','rent_2bed_gbp'),('Three bedrooms','rent_3bed_gbp'),('Four or more','rent_4plus_gbp')]
    else:
        columns=[('Detached','rent_detached_gbp'),('Semi-detached','rent_semi_gbp'),('Terraced','rent_terraced_gbp'),('Flat / maisonette','rent_flat_gbp')]
    values=[float(row[col]) if pd.notna(row[col]) else None for _,col in columns]
    fig=go.Figure(go.Bar(x=[a for a,b in columns], y=values,marker_color=['#9fbedc','#639fcd',BLUE,NAVY],
        text=['£'+f'{x:,.0f}' if x is not None else 'N/A' for x in values],textposition='outside',
        hovertemplate='%{x}<br>£%{y:,.0f}/month<extra></extra>'))
    max_val=max((x for x in values if x is not None), default=1)
    fig.update_layout(height=325,margin=dict(l=8,r=15,t=25,b=24),
        font=dict(color=NAVY),plot_bgcolor='white',paper_bgcolor='white',showlegend=False,
        xaxis=dict(title=None),yaxis=dict(title='Average monthly rent (£)',tickprefix='£',tickformat=',',
                                          range=[0,max_val*1.18],gridcolor='#edf2f8'))
    return fig


def map_costs(current, field, selected, geo, mode):
    boroughs=current[current.code.str.startswith('E09')].dropna(subset=[field]).copy()
    fig=go.Figure()
    if mode=='rent':
        # One borough has no published series. Neutral-grey polygon; NEVER assume rent is zero.
        fig.add_trace(go.Choropleth(geojson=geo,locations=[CITY_CODE],z=[1],
            featureidkey='properties.gss_code', colorscale=[[0,'#e4e7ec'],[1,'#e4e7ec']],showscale=False,
            marker_line_color='white',marker_line_width=1.0,
            hovertemplate='City of London<br>No borough rent data available<extra></extra>',
            name='Unavailable'))
    fig.add_trace(go.Choropleth(geojson=geo,locations=boroughs.code,z=boroughs[field],
        featureidkey='properties.gss_code', colorscale=[[0,'#e5f2fa'],[.23,'#abd6e8'],[.55,'#509cce'],[1,'#184878']],
        marker_line_color='#ffffff',marker_line_width=0.85,
        colorbar=dict(title=dict(text='Rent (£/month)' if mode=='rent' else 'Price (£)'),
                      thickness=14,len=.77,tickprefix='£',tickformat=','),
        customdata=boroughs[['borough']].to_numpy(),
        hovertemplate='<b>%{customdata[0]}</b><br>£%{z:,.0f}'+('/month' if mode=='rent' else '')+'<extra></extra>'))
    if selected not in (LONDON_CODE,CITY_CODE if mode=='rent' else ''):
        b=boroughs[boroughs.code==selected]
        if len(b):
            fig.add_trace(go.Choropleth(geojson=geo,locations=b.code,z=[1],featureidkey='properties.gss_code',
                colorscale=[[0,'rgba(0,0,0,0)'],[1,'rgba(0,0,0,0)']],showscale=False,
                marker_line_color=ORANGE,marker_line_width=3.0,
                customdata=b[['borough',field]].to_numpy(),
                hovertemplate='<b>%{customdata[0]}</b><br>£%{customdata[1]:,.0f}<extra></extra>'))
    fig.update_geos(fitbounds='locations',visible=False,projection_type='mercator',bgcolor='#f4f8fc',
                    showland=True,landcolor='#f4f8fc',showocean=True,oceancolor='#f4f8fc',showlakes=False,showcoastlines=False)
    fig.update_layout(height=590,margin=dict(l=0,r=46,t=10,b=0),paper_bgcolor='#f4f8fc',showlegend=False,
                      font=dict(color=NAVY),dragmode=False)
    return fig


def metric_panel(current, data, mode, selected, date):
    field='rent_gbp' if mode=='rent' else 'average_price_gbp'
    boroughs=current.loc[current.code.str.startswith('E09') & current[field].notna()].sort_values(field,ascending=False)
    london=comparison_row(current,LONDON_CODE,field)
    focus=comparison_row(current,selected,field)
    if focus is None:
        st.info('No figure is available for this area and month. Select another borough to view its costs.')
        return False
    code=selected
    yearly=(float(focus['rent_annual_change_pct']) if mode=='rent' and pd.notna(focus['rent_annual_change_pct'])
             else annual_price_change(data, code, date, field) if mode=='buy' else None)
    cols=st.columns(4)
    cols[0].metric('Average monthly private rent' if mode=='rent' else 'Average property price',
                   f'£{focus[field]:,.0f}',help='London regional estimate' if selected==LONDON_CODE else 'Estimate for the selected local authority')
    cols[1].metric('Annual rent change' if mode=='rent' else 'Annual house-price change',
                   f'{yearly:+.1f}%' if yearly is not None else 'N/A',
                   help='Compared with the same month one year before; not month-on-month.')
    if selected==LONDON_CODE:
        highest=boroughs.iloc[0]; lowest=boroughs.iloc[-1]
        cols[2].metric('Highest-cost borough',highest.borough,help=f'£{highest[field]:,.0f}')
        cols[3].metric('Lowest-cost borough',lowest.borough,help=f'£{lowest[field]:,.0f}')
    else:
        comparator=float(london[field]) if london is not None else None
        diff=100*(float(focus[field])/comparator-1) if comparator else None
        cols[2].metric('Vs London benchmark',f'{diff:+.1f}%' if diff is not None else 'N/A',
                       help='Difference from the independently published London regional estimate.')
        rank=boroughs.reset_index(drop=True).index[boroughs.reset_index(drop=True).code==selected]
        cols[3].metric('Borough cost rank',f'{int(rank[0])+1} of {len(boroughs)}' if len(rank) else 'N/A',
                       help='Rank 1 has the highest cost.')
    return True


def render_cost_tab(data, mode, selected, trend_comparisons, period, codes):
    field='rent_gbp' if mode=='rent' else 'average_price_gbp'
    max_date=data.date.max()
    latest_month=fmt_month(max_date)
    month_options=sorted(data.date.drop_duplicates(),reverse=True)
    date=st.selectbox('Reference month', month_options,format_func=fmt_month,index=0,key=f'{mode}_reference_month',
        help='Updates summary cards, borough ranking, and map. Historical trends remain available for the selected period.')
    current=get_latest(data,date)
    london=comparison_row(current,LONDON_CODE,field)
    st.caption(f'{fmt_month(date)} data · '+('Private rent estimates' if mode=='rent' else 'UK HPI average property-price estimates')+
               (' · 32 boroughs (City of London not available)' if mode=='rent' else ' · 33 local authority areas'))
    if selected==CITY_CODE and mode=='rent':
        st.info('The ONS rent workbook has no separate City of London estimate. Borough comparisons, London averages and the rental map remain available; City of London is shown as unavailable.')
    else:
        metric_panel(current,data,mode,selected,date)

    st.divider()
    st.markdown('<div class="section-kicker">VIEW 01 · COST RANKING</div>',unsafe_allow_html=True)
    st.subheader('Where is housing most expensive?')
    st.caption('Compare published borough averages with the separately published London-wide estimate (orange dashed line). Hover over a bar to see the exact price or rent for that borough.')
    if london is not None:
        st.caption(f'**Orange line: London average £{float(london[field]):,.0f}'+('/month' if mode=='rent' else ' per property')+'** — officially published regional value; not a simple average of boroughs.')
    st.plotly_chart(bar_ranking(current,field,selected,float(london[field]) if london is not None else None,mode),
                    use_container_width=True,config={'displayModeBar':False})

    st.divider()
    st.markdown('<div class="section-kicker">VIEW 02 · TRENDS</div>',unsafe_allow_html=True)
    st.subheader('How have costs changed over time?')
    st.caption('Regional benchmark and chosen boroughs. Select a different time horizon in the sidebar.')
    trend_selection = (LONDON_CODE if mode=='rent' and selected==CITY_CODE else selected)
    st.plotly_chart(trend_chart(data,field,trend_selection,trend_comparisons,period),
                    use_container_width=True,config={'displayModeBar':False})

    if mode=='rent':
        st.divider()
        st.markdown('<div class="section-kicker">VIEW 03 · PROPERTY SIZE</div>',unsafe_allow_html=True)
        st.subheader('How does monthly rent vary by bedroom count?')
        current_row=comparison_row(current,selected if selected!=CITY_CODE else LONDON_CODE,field)
        if current_row is not None:
            area_label='London' if selected in (LONDON_CODE,CITY_CODE) else current_row.borough
            st.caption(f'Average monthly private rent by bedroom count · {area_label} · {fmt_month(date)}.'+
                       (' City of London is unavailable; displaying the London benchmark.' if selected==CITY_CODE else ''))
            st.plotly_chart(breakdown_chart(current_row),use_container_width=True,config={'displayModeBar':False})
            st.markdown('**Average private rent by property type**')
            st.plotly_chart(breakdown_chart(current_row,kind='property'),use_container_width=True,config={'displayModeBar':False})
            st.caption('These are **rental price estimates**, not the number of homes rented. A detached average can sometimes be lower than a semi-detached average because the underlying homes differ in area, size, quality and market mix; the bars are not matched like-for-like properties. We cannot identify the most-rented type from price estimates.')

    if mode=='buy':
        st.divider()
        st.markdown('<div class="section-kicker">VIEW 03 · PROPERTY TYPES AND SALES ACTIVITY</div>',unsafe_allow_html=True)
        st.subheader('What types of homes cost more to buy?')
        bytype=pd.read_csv(DATA_DIR/'london_purchase_prices_by_type.csv',parse_dates=['date'])
        chosen=bytype[bytype.date.eq(pd.Timestamp(date))].copy()
        if not chosen.empty:
            f=go.Figure(go.Bar(x=chosen['type'],y=chosen['average_price_gbp'],
                  marker_color=['#8eb7d6','#4d96c9',BLUE,NAVY],
                  text=[f'£{v:,.0f}' for v in chosen.average_price_gbp],textposition='outside',
                  hovertemplate='%{x}: £%{y:,.0f}<extra></extra>'))
            f.update_layout(height=345,margin=dict(l=5,r=5,t=30,b=20),plot_bgcolor='white',paper_bgcolor='white',
                font=dict(color=NAVY),yaxis=dict(title='London average price (£)',gridcolor='#eff2f7',rangemode='tozero',tickprefix='£',tickformat=','))
            st.plotly_chart(f,use_container_width=True,config={'displayModeBar':False})
            st.caption(f'**London-wide** prices by type for {fmt_month(date)}, from the UK HPI “By type” worksheet. These are not borough-specific prices and cannot tell us which type is most frequently purchased.')
        else:
            st.info('No property-type price series for the selected month in the bundled HPI By type worksheet.')
        with st.expander('How many homes were bought in each borough? (total sales, not by type)'):
            volumes=pd.read_csv(DATA_DIR/'borough_sales_volume.csv',dtype={'code':str},parse_dates=['date'])
            years=sorted(volumes.date.dt.year.unique())
            complete=[y for y in years if volumes[volumes.date.dt.year.eq(y)].date.dt.month.nunique()==12]
            default=max([y for y in complete if y<max(years)],default=max(complete))
            chosen_year=st.selectbox('Calendar year',sorted(complete,reverse=True),index=sorted(complete,reverse=True).index(default),key='sales_volume_year')
            sales=volumes[volumes.date.dt.year.eq(chosen_year)].groupby('code',as_index=False)['sales'].sum()
            boroughnames=data[['code','borough']].drop_duplicates('code')
            sales=sales.merge(boroughnames,on='code',how='left').sort_values('sales')
            f=go.Figure(go.Bar(y=sales.borough,x=sales.sales,orientation='h',marker_color=MUTED,
                    hovertemplate='%{y}: %{x:,.0f} registered sales<extra></extra>'))
            f.update_layout(height=860,margin=dict(l=5,r=10,t=15,b=10),plot_bgcolor='white',paper_bgcolor='white',
                    font=dict(color=NAVY),xaxis=dict(title=f'{chosen_year} total registered property sales',gridcolor='#edf2f7'))
            st.plotly_chart(f,use_container_width=True,config={'displayModeBar':False})
            st.caption('Source: UK HPI “Sales Volume” worksheet. These are **total residential sales**, not sales by property type; recent months may be incomplete and revised.')
        st.info('The current workbooks cannot establish the “most bought” housing **type**, nor the “most rented” type in each borough. This would require separate type-specific transaction/tenancy counts; average prices and rents are not counts.',icon='ℹ️')

    st.divider()
    st.markdown(f'<div class="section-kicker">VIEW {"04" if mode=="rent" else "03"} · SPATIAL DISTRIBUTION</div>',unsafe_allow_html=True)
    st.subheader('Where are housing costs highest across London?')
    st.caption('Darker boroughs mean higher published average costs. Colours show absolute prices or monthly rents, not affordability.')
    expected=tuple(sorted(codes))
    geo, origin, geometry_error = costs_boundaries(expected)
    if geo is None:
        st.warning('The official borough boundary service is currently unavailable and no cached file is present. The price and rent charts still work.')
        with st.expander('Provide a London borough boundary GeoJSON (optional)'):
            upload=st.file_uploader('Upload London borough GeoJSON containing the 33 GSS codes',type=['json','geojson'],key=f'map_upload_{mode}')
            if upload is not None:
                try:
                    geo=load_uploaded_geojson(upload.read(),expected)
                    st.plotly_chart(map_costs(current,field,selected,geo,mode),use_container_width=True,config={'displayModeBar':False})
                except Exception as e:st.error(f'Boundary validation failed: {e}')
            st.caption(f'[Official GLA borough boundary data]({BOUNDARY_SOURCE}). Download once to enable offline use.')
            st.code(geometry_error[:450] if geometry_error else 'Boundary geometry not available.')
    else:
        st.plotly_chart(map_costs(current,field,selected,geo,mode),use_container_width=True,config={'displayModeBar':False})
        st.caption(f'Boundary source: {origin} · [GLA data]({BOUNDARY_SOURCE}) (OGL v3).'+
                   (' City of London is grey because borough rent data are not provided.' if mode=='rent' else ''))

    with st.expander('Methodology and sources'):
        if mode=='rent':
            st.markdown(f'''**ONS Price Index of Private Rents (PIPR)** — [source]({RENT_SOURCE}).

- The values are **estimated average monthly rents**, rounded to the nearest £1, not asking rents for new listings.
- Data: January 2015–{latest_month}; 32 London boroughs plus a separately published London regional series.
- No City of London borough series; missing values must **never** be treated as £0.
- The annual rent percentage uses the source's published annual change. Monthly data are not seasonally adjusted.
- Bedroom-count and property-type averages are different breakdowns; they should not be summed.
- Rental cost alone does not establish housing affordability; that would require household incomes.''')
        else:
            st.markdown(f'''**UK House Price Index (Land Registry / ONS)** — [source]({PRICE_SOURCE}).

- Average price is the **UK HPI modelled average property price**, not the arithmetic average of all property-sale transactions in that month.
- Data: January 1995–{latest_month}; 33 London local authority areas plus a separately published London regional series.
- Annual price change shown is calculated from the same geography's published average price in the equivalent month a year earlier.
- Local-authority price series use a three-month moving average; recent months may be revised as registrations arrive.
- Prices are nominal (not inflation-adjusted). Purchase prices do not capture mortgage repayments or all buying costs.''')



def render_cost_dashboard():
    price,rent=load_cost_data()
    names=price.loc[price.code.str.startswith('E09'),['borough','code']].drop_duplicates().sort_values('borough')
    display={r.borough:r.code for r in names.itertuples(index=False)}
    options=[LONDON_LABEL]+list(display)
    st.sidebar.markdown('### Explore housing costs')
    area=st.sidebar.selectbox('Geography', options, key='cost_selected_area',
                              help='The same selected area applies to both Buying and Renting.')
    selected=LONDON_CODE if area==LONDON_LABEL else display[area]
    period=st.sidebar.selectbox('Trend period',['Last 5 years','Last 3 years','Last 10 years','All available'],key='cost_period')
    other=[a for a in display if display[a]!=selected and display[a]!=CITY_CODE]
    compares=st.sidebar.multiselect('Add boroughs to trend (optional)',other,max_selections=2,key='cost_trends')
    extras=[display[a] for a in compares]
    st.sidebar.divider()
    st.sidebar.caption('Published borough and London averages are independent estimates; they are not summed or averaged together.')
    st.sidebar.caption('Rent: ONS PIPR · August 2026. Buying: UK HPI · July 2026. Income: PAYE Sep 2026; full-time earnings by borough (ASHE 2025).')
    st.sidebar.link_button('Official rental source',RENT_SOURCE,use_container_width=True)
    st.sidebar.link_button('Official house-price source',PRICE_SOURCE,use_container_width=True)
    st.sidebar.link_button('ONS full-time earnings source','https://www.ons.gov.uk/employmentandlabourmarket/peopleinwork/earningsandworkinghours/datasets/placeofresidencebylocalauthorityashetable8',use_container_width=True)

    st.markdown('<div class="section-kicker">OBJECTIVE 02 · HOUSING COSTS</div>',unsafe_allow_html=True)
    st.title('Housing costs and pay in London')
    st.markdown('<p class="main-intro">What does it cost to rent or buy, how much do Londoners earn, and what can those numbers tell us about the pressure on housing? We will keep income, costs and affordability clearly separate.</p>',unsafe_allow_html=True)
    st.caption('Rent and purchase prices: ONS and UK HPI · Pay: HMRC/ONS PAYE 2026 and ONS ASHE 2025 · borough comparisons where published')
    renting,buying,income=st.tabs(['🏠  Renting','🔑  Buying','💷  Income'])
    stock=pd.read_csv(DATA_DIR/'london_dwelling_stock_2012_2025.csv',dtype={'code':str},usecols=['code'])
    expected_codes=set(stock.code.unique())
    with renting:
        render_cost_tab(rent,'rent',selected,extras,period,expected_codes)
    with buying:
        render_cost_tab(price,'buy',selected,extras,period,expected_codes)
    with income:
        from income_dashboard import render_income_tab
        render_income_tab(selected,expected_codes)
    render_reference_guide()
