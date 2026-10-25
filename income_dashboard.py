"""Income tab: source-verified London payroll pay and borough resident earnings.

Strictly separate three populations/series:
- HMRC/ONS PAYE RTI median monthly pay for all payrolled employees, London and UK.
- ONS ASHE median *weekly gross pay of full-time residents*, 2025, converted
  by us to a monthly equivalent (52 weeks / 12 months).
- GLA Housing in London 2025 Figure 3.11 historical earnings/rent series,
  whose original methodological note refers to workplace earnings.
Do not use the ratio of an aggregate rent estimate and an aggregate employee
median as a real household affordability rate.
"""
from __future__ import annotations

from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from cost_dashboard import CITY_CODE, LONDON_CODE, NAVY, BLUE, ORANGE, MUTED, TEAL, costs_boundaries

DATA_DIR=Path(__file__).resolve().parent/'data'
SOURCE_ASHE='https://www.ons.gov.uk/employmentandlabourmarket/peopleinwork/earningsandworkinghours/datasets/placeofresidencebylocalauthorityashetable8'
SOURCE_PAYE='https://data.london.gov.uk/download/v8wzm/q24/2026.10%20LMU.html'
SOURCE_GLA='https://www.london.gov.uk/sites/default/files/2026-01/Housing%20in%20London%202025%20report%20%28002%29.pdf'
SOURCE_RENT='https://www.ons.gov.uk/economy/inflationandpriceindices/datasets/priceindexofprivaterentsukmonthlypricestatistics'
BOUNDARY_SOURCE='https://data.london.gov.uk/dataset/london-boroughs-e55pw'

@st.cache_data(show_spinner=False)
def load_income_data():
    annual=pd.read_csv(DATA_DIR/'resident_fulltime_earnings_ashe_2025.csv',dtype={'code':str})
    historical=pd.read_csv(DATA_DIR/'london_pay_history_gla_2015_2025.csv',parse_dates=['date'])
    recent=pd.read_csv(DATA_DIR/'london_payroll_latest_2026.csv',parse_dates=['month'])
    if len(annual)!=33 or len(annual.code.unique())!=33 or CITY_CODE in annual.code.values:
        raise ValueError('Expected 32 ONS ASHE borough observations plus London regional estimate; City of London is not in the source extract.')
    if float(annual.loc[annual.code==LONDON_CODE,'median_gross_weekly_fulltime_gbp'].iloc[0])!=902.7:
        raise ValueError('London 2025 ASHE reference not reconciled.')
    annual['monthly_equivalent_gbp'] = annual['median_gross_weekly_fulltime_gbp'] * 52 / 12
    if not historical.date.is_monotonic_increasing or historical.date.duplicated().any():
        raise ValueError('Historical earnings trend has invalid chronology.')
    return annual,historical,recent


def money(value):
    return f'£{value:,.0f}'


def make_ranking(annual:pd.DataFrame,selected:str):
    boroughs=annual.loc[annual.code.ne(LONDON_CODE)].sort_values('monthly_equivalent_gbp',ascending=True).copy()
    london=float(annual.loc[annual.code.eq(LONDON_CODE),'monthly_equivalent_gbp'].iloc[0])
    colors=[BLUE if code==selected else '#9ab6d6' for code in boroughs.code]
    fig=go.Figure(go.Bar(y=boroughs.borough,x=boroughs.monthly_equivalent_gbp,orientation='h',
        marker_color=colors,customdata=boroughs[['median_gross_weekly_fulltime_gbp']].to_numpy(),
        hovertemplate='<b>%{y}</b><br>Monthly equivalent: £%{x:,.0f}<br>Published median weekly pay: £%{customdata[0]:,.1f}<extra></extra>'))
    fig.add_vline(x=london,line=dict(color=ORANGE,width=2,dash='dash'))
    fig.add_annotation(x=london,y=1.075,yref='paper',text=f'London ASHE 2025: {money(london)}/month',showarrow=False,font=dict(size=11,color=ORANGE),bgcolor='#f6f8fc')
    fig.update_layout(height=935,margin=dict(l=8,r=16,t=56,b=18),font=dict(color=NAVY),
        paper_bgcolor='#f6f8fc',plot_bgcolor='#f6f8fc',showlegend=False,
        xaxis=dict(title='Approximate gross monthly full-time pay (£)',tickprefix='£',tickformat=',',gridcolor='#e5ebf3',rangemode='tozero'),
        yaxis=dict(title=None,tickfont=dict(size=11)))
    return fig


def make_history_chart(hist, view):
    d=hist.sort_values('date').copy()
    fig=go.Figure()
    if view=='Earnings and rent growth (index)':
        baseline_pay=float(d.iloc[0].london_median_monthly_pay_gbp)
        baseline_rent=float(d.iloc[0].london_monthly_rent_gbp)
        d['pay_index']=d.london_median_monthly_pay_gbp/baseline_pay*100
        d['rent_index']=d.london_monthly_rent_gbp/baseline_rent*100
        fig.add_trace(go.Scatter(x=d.date,y=d.pay_index,mode='lines',name='Monthly earnings',
            line=dict(color=BLUE,width=3),customdata=d[['london_median_monthly_pay_gbp']].to_numpy(),
            hovertemplate='%{x|%b %Y}<br>Index: %{y:.1f}<br>Pay in source: £%{customdata[0]:,.0f}<extra></extra>'))
        fig.add_trace(go.Scatter(x=d.date,y=d.rent_index,mode='lines',name='Average private rent',
            line=dict(color=TEAL,width=3),customdata=d[['london_monthly_rent_gbp']].to_numpy(),
            hovertemplate='%{x|%b %Y}<br>Index: %{y:.1f}<br>Rent in source: £%{customdata[0]:,.0f}<extra></extra>'))
        title='January 2015 = 100 (nominal values, no inflation adjustment)'
    else:
        fig.add_trace(go.Scatter(x=d.date,y=d.london_median_monthly_pay_gbp,mode='lines',name='GLA earnings series',
            line=dict(color=BLUE,width=3),hovertemplate='%{x|%b %Y}<br>£%{y:,.0f} a month<extra></extra>'))
        title='Gross monthly pay, GLA historical series (£)'
    fig.update_layout(height=395,margin=dict(l=10,r=15,t=26,b=25),
        title=dict(text=title,font=dict(size=13)),font=dict(color=NAVY),paper_bgcolor='white',plot_bgcolor='white',
        xaxis=dict(title=None,gridcolor='#edf2f8'),
        yaxis=dict(title='2015 = 100' if view.startswith('Earnings and') else 'Pay (£/month)',gridcolor='#edf2f8'),
        legend=dict(orientation='h',y=-.27),hovermode='x unified')
    return fig


def make_gender_chart(annual,selected):
    london=annual.loc[annual.code.eq(LONDON_CODE)].iloc[0]
    chosen=annual.loc[annual.code.eq(selected)].iloc[0] if selected!=CITY_CODE else london
    labels=['Women','Men']
    colnames=['median_gross_weekly_fulltime_female_gbp','median_gross_weekly_fulltime_male_gbp']
    fig=go.Figure()
    for group,row,col in [('London',london,MUTED),
                          (str(chosen.borough),chosen,BLUE)]:
        if group=='London' and selected in [LONDON_CODE,CITY_CODE]:continue
        fig.add_trace(go.Bar(name=group,x=labels,y=[float(row[c])*52/12 for c in colnames],
            marker_color=col,text=[money(float(row[c])*52/12) for c in colnames],textposition='outside',
            hovertemplate=group+'<br>%{x}: £%{y:,.0f}/month equivalent<extra></extra>'))
    fig.update_layout(height=340,barmode='group',margin=dict(l=8,r=8,t=32,b=12),font=dict(color=NAVY),
        paper_bgcolor='white',plot_bgcolor='white',yaxis=dict(title='Median full-time monthly equivalent (£)',tickprefix='£',tickformat=',',gridcolor='#eef2f8',rangemode='tozero'),
        legend=dict(orientation='h',y=-.2))
    return fig


def make_income_map(annual,selected,geo):
    boroughs=annual[annual.code!=LONDON_CODE]
    fig=go.Figure()
    fig.add_trace(go.Choropleth(geojson=geo,locations=[CITY_CODE],z=[1],featureidkey='properties.gss_code',
       colorscale=[[0,'#e3e8ed'],[1,'#e3e8ed']],showscale=False,
       marker_line_color='white',marker_line_width=.9,
       hovertemplate='City of London<br>No borough ASHE estimate in this extract<extra></extra>'))
    fig.add_trace(go.Choropleth(geojson=geo,locations=boroughs.code,z=boroughs.monthly_equivalent_gbp,
       featureidkey='properties.gss_code',colorscale=[[0,'#e7f2fa'],[.3,'#abcde3'],[.6,'#66a6d4'],[1,'#1b477c']],
       marker_line_color='white',marker_line_width=.9,
       colorbar=dict(title=dict(text='Gross pay/month (£)'),tickprefix='£',tickformat=',',len=.75),
       customdata=boroughs[['borough','median_gross_weekly_fulltime_gbp']].to_numpy(),
       hovertemplate='<b>%{customdata[0]}</b><br>Monthly equivalent £%{z:,.0f}<br>Published weekly median £%{customdata[1]:,.1f}<extra></extra>'))
    if selected not in (LONDON_CODE,CITY_CODE):
        row=boroughs.loc[boroughs.code.eq(selected)]
        if not row.empty:
            fig.add_trace(go.Choropleth(geojson=geo,locations=row.code,z=[1],featureidkey='properties.gss_code',
                colorscale=[[0,'rgba(0,0,0,0)'],[1,'rgba(0,0,0,0)']],showscale=False,
                marker_line_color=ORANGE,marker_line_width=3,
                customdata=row[['borough','monthly_equivalent_gbp']].to_numpy(),
                hovertemplate='<b>%{customdata[0]}</b><br>£%{customdata[1]:,.0f}/month equivalent<extra></extra>'))
    fig.update_geos(fitbounds='locations',visible=False,projection_type='mercator',bgcolor='#f5f8fc',
                    showland=True,landcolor='#f5f8fc',showcoastlines=False,showlakes=False)
    fig.update_layout(height=570,margin=dict(l=0,r=40,t=10,b=0),paper_bgcolor='#f5f8fc',dragmode=False,
        showlegend=False,font=dict(color=NAVY))
    return fig


def render_income_tab(selected: str, expected_codes: set[str]):
    annual,hist,recent=load_income_data()
    st.markdown('### How much do people in London actually earn?')
    st.caption('A look at pay, not total household income. This section uses ONS/HMRC payroll statistics and the Annual Survey of Hours and Earnings (ASHE).')
    months=sorted(recent.month,reverse=True)
    chosen=st.selectbox('Pay reference month (London-wide figures)',months,index=0,
        format_func=lambda x:x.strftime('%B %Y'),key='income_pay_month')
    current=recent.loc[recent.month.eq(chosen)].iloc[0]
    pay=float(current.london_median_monthly_pay_gbp)
    uk=current.uk_median_monthly_pay_gbp
    annual_growth=current.london_annual_change_pct
    c1,c2,c3,c4=st.columns(4)
    c1.metric('Typical London monthly pay',money(pay),help='Median gross monthly pay of PAYE employees, based on their place of residence—not average household income.')
    c2.metric('Annual change in London pay',f'{annual_growth:+.1f}%' if pd.notna(annual_growth) else 'Not provided',help='Published year-on-year payroll pay change; not a real-terms change.')
    c3.metric('Typical UK monthly pay',money(uk) if pd.notna(uk) else 'Not provided',help='UK median PAYE monthly pay from same published release.')
    c4.metric('London vs UK pay',f'{(pay/uk-1)*100:+.1f}%' if pd.notna(uk) else 'Not provided',help='Percentage difference between published regional and UK medians; these medians are independent estimates.')
    st.caption(f'{chosen.strftime("%B %Y")} · HMRC / ONS PAYE Real Time Information, London residents · Gross pay (before tax/NI); includes full- and part-time employees. [GLA source]({SOURCE_PAYE})')
    st.info('**Why median, not mean?** Median is the middle employee pay figure, so very high salaries have less influence. This is **employee pay**, not take-home income, household income or the average income of people who rent.',icon='ℹ️')

    st.divider()
    st.markdown('<div class="section-kicker">VIEW 01 · PAY BY BOROUGH</div>',unsafe_allow_html=True)
    st.subheader('Where do full-time Londoners earn more?')
    london=annual.loc[annual.code.eq(LONDON_CODE)].iloc[0]
    rank=annual.loc[annual.code.ne(LONDON_CODE)].sort_values('monthly_equivalent_gbp',ascending=False)
    current_row=annual.loc[annual.code.eq(selected)]
    if selected==CITY_CODE:
        st.warning('City of London is not included in this 2025 ASHE borough extract. The full London and other borough figures remain available.')
    elif selected==LONDON_CODE:
        top=rank.iloc[0];bottom=rank.iloc[-1]
        a,b,c=st.columns(3)
        a.metric('London full-time pay / month (2025)',money(float(london.monthly_equivalent_gbp)))
        b.metric('Highest borough median',str(top.borough),help=money(float(top.monthly_equivalent_gbp)))
        c.metric('Lowest borough median',str(bottom.borough),help=money(float(bottom.monthly_equivalent_gbp)))
    elif not current_row.empty:
        chosen_row=current_row.iloc[0]
        p=float(chosen_row.monthly_equivalent_gbp); ref=float(london.monthly_equivalent_gbp)
        a,b,c=st.columns(3)
        a.metric(f'{chosen_row.borough} full-time pay / month (2025)',money(p))
        b.metric('Compared with London full-time pay',f'{(p/ref-1)*100:+.1f}%')
        c.metric('Full-time pay rank',f'{int(rank.reset_index(drop=True).index[rank.reset_index(drop=True).code.eq(selected)][0])+1} of 32')
    st.caption('The borough bars are **2025 ONS ASHE median gross weekly pay of full-time residents**, converted by us into an approximate monthly amount (weekly × 52 ÷ 12). This is **not** the same series as the September 2026 PAYE headline cards.')
    st.plotly_chart(make_ranking(annual,selected),use_container_width=True,config={'displayModeBar':False})
    st.markdown('**2025 full-time earnings by borough**')
    detail=rank[['borough','median_gross_weekly_fulltime_gbp','monthly_equivalent_gbp']].rename(columns={'borough':'Borough','median_gross_weekly_fulltime_gbp':'Published median weekly (£)','monthly_equivalent_gbp':'Calculated monthly equivalent (£)'})
    st.dataframe(detail,hide_index=True,use_container_width=True, column_config={
        'Published median weekly (£)':st.column_config.NumberColumn(format='£%.1f'),
        'Calculated monthly equivalent (£)':st.column_config.NumberColumn(format='£%.0f')},height=320)

    st.divider()
    st.markdown('<div class="section-kicker">VIEW 02 · TRENDS</div>',unsafe_allow_html=True)
    st.subheader('Has pay kept up with rising rents?')
    st.caption('The GLA has a historical monthly earnings-and-rents series running from January 2015 to August 2025. Compare their **growth over time**, not how much an individual tenant spends.')
    perspective=st.radio('Show the historical series as', ['Earnings and rent growth (index)','Monthly earnings (£)'], horizontal=True,key='income_trend_view')
    st.plotly_chart(make_history_chart(hist,perspective),use_container_width=True,config={'displayModeBar':False})
    st.caption('Source: [GLA, *Housing in London 2025*, figure/table 3.11]('+SOURCE_GLA+'). The report compiles earnings and private-rent series, with an earnings geography/methodology different from the resident ASHE comparison. Historical data end in August 2025; the latest 2026 PAYE cards are displayed separately and are not spliced into the old trend.')

    st.divider()
    st.markdown('<div class="section-kicker">VIEW 03 · PAY GROUPS</div>',unsafe_allow_html=True)
    st.subheader('How does typical full-time pay differ between women and men?')
    st.caption('Published ASHE 2025 median gross weekly earnings, converted to monthly equivalents. Select a borough using the sidebar.')
    chosen_row=annual.loc[annual.code.eq(selected if selected!=CITY_CODE else LONDON_CODE)].iloc[0]
    st.plotly_chart(make_gender_chart(annual,selected),use_container_width=True,config={'displayModeBar':False})
    if selected!=CITY_CODE:
        st.table(pd.DataFrame([
            {'Group':'All full-time employees','Median weekly pay':money(float(chosen_row.median_gross_weekly_fulltime_gbp)),'Approximate monthly equivalent':money(float(chosen_row.median_gross_weekly_fulltime_gbp)*52/12)},
            {'Group':'Women working full-time','Median weekly pay':money(float(chosen_row.median_gross_weekly_fulltime_female_gbp)),'Approximate monthly equivalent':money(float(chosen_row.median_gross_weekly_fulltime_female_gbp)*52/12)},
            {'Group':'Men working full-time','Median weekly pay':money(float(chosen_row.median_gross_weekly_fulltime_male_gbp)),'Approximate monthly equivalent':money(float(chosen_row.median_gross_weekly_fulltime_male_gbp)*52/12)},
        ]))
    st.caption('These are different groups of people, not comparisons of women and men doing identical jobs. They are not a like-for-like gender-pay-gap estimate.')

    st.divider()
    st.markdown('<div class="section-kicker">VIEW 04 · SPATIAL DISTRIBUTION</div>',unsafe_allow_html=True)
    st.subheader('Where is full-time pay higher across London?')
    st.caption('Darker boroughs indicate higher **median gross pay for full-time residents in 2025**, converted from weekly ASHE estimates. Not average household income.')
    geo,origin,err=costs_boundaries(tuple(sorted(expected_codes)))
    if geo is None:
        st.warning('A London borough boundary GeoJSON is not currently available. The borough rankings and table above still work.')
        st.caption(f'[Get official GLA borough boundaries]({BOUNDARY_SOURCE}) and save the GeoJSON in the project’s data/sources folder to enable maps without the internet.')
    else:
        st.plotly_chart(make_income_map(annual,selected,geo),use_container_width=True,config={'displayModeBar':False})
        st.caption(f'Boundary source: {origin} · [GLA boundary data]({BOUNDARY_SOURCE}). City of London has no corresponding 2025 borough value in this extract.')

    st.divider()
    st.markdown('<div class="section-kicker">VIEW 05 · PAY AND HOUSING COSTS</div>',unsafe_allow_html=True)
    st.subheader('How do London pay and private rent compare?')
    rent=pd.read_csv(DATA_DIR/'private_rents.csv',parse_dates=['date'],dtype={'code':str})
    refdate=pd.Timestamp('2026-08-01')
    row=rent[(rent.code==LONDON_CODE)&(rent.date==refdate)]
    if not row.empty:
        rentvalue=float(row.iloc[0].rent_gbp)
        fig=go.Figure(go.Bar(x=['London median monthly employee pay (Sep 2026)','London average private rent (Aug 2026)'],
            y=[3120,rentvalue],marker_color=[BLUE,ORANGE],text=[money(3120),money(rentvalue)],
            textposition='outside',hovertemplate='%{x}<br>£%{y:,.0f}/month<extra></extra>'))
        fig.update_layout(height=360,margin=dict(l=10,r=10,t=25,b=80),font=dict(color=NAVY),
            paper_bgcolor='white',plot_bgcolor='white',showlegend=False,
            yaxis=dict(title='Published monthly amount (£)',tickprefix='£',tickformat=',',gridcolor='#eff2f8',rangemode='tozero'))
        st.plotly_chart(fig,use_container_width=True,config={'displayModeBar':False})
        st.info('**This is a comparison of two London-wide statistics, NOT a household budget.** The people included in the payroll median are not necessarily the tenants included in the average rent. It would be misleading to say a typical tenant spends this percentage of their wages on rent. A proper rent-to-income affordability analysis needs matched household or tenant-level income information.',icon='ℹ️')
        st.caption(f'London median PAYE employee pay: [GLA/HMRC/ONS]({SOURCE_PAYE}). London average monthly private rent: [ONS PIPR]({SOURCE_RENT}). Different reference months, populations and methods.')

    with st.expander('Definitions, sources and reliability'):
        st.markdown(f'''**What does “income” mean here?** This tab primarily measures **gross employee pay before deductions**, not all income. It excludes the earnings of people without PAYE jobs, and the full-time ASHE charts exclude part-time work and self-employment. Household income may combine several earners, self-employment, pensions and benefits.

**Pay is not all take-home income.** Gross pay does not deduct income tax, National Insurance, pension contributions or other deductions.

**Why do the London numbers differ?** The **2026 PAYE** median covers payrolled employees, including part-time staff. The **2025 ASHE** median covers full-time employees who live in London. These are **different populations and different years**, not contradictory estimates.

**Which borough?** ASHE ranks people by their **home borough**, not where they work. The GLA historical earnings series reports its own underlying earnings geography and should not be mixed with the residence-based series to calculate borough trends.

**What did we calculate?** Each 2025 borough monthly amount is **median gross weekly pay × 52 ÷ 12**, an approximate monthly equivalent. It is not an independently published monthly ASHE observation. We do not average borough medians to obtain the London figure; the London regional median is independently published.

**Source reliability.** [ONS ASHE Table 8]({SOURCE_ASHE}) is an official sample-based earnings survey and local figures can be uncertain. [HMRC/ONS PAYE RTI]({SOURCE_PAYE}) draws on administrative payroll submissions but its latest figures are revised. Historical trends come from [GLA *Housing in London 2025*]({SOURCE_GLA}), drawing on PAYE and ONS private rents. Neither pay series measures a typical private renter's disposable household income.''')
