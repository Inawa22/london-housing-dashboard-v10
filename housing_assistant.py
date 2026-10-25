"""Source-grounded data companion, usable offline with optional OpenAI API reasoning.
No private data or API key is included in the project. Never fabricate missing data.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen
import pandas as pd
import streamlit as st

from housing_explainer import DEFINITIONS, SOURCE_TABLE

ROOT=Path(__file__).resolve().parent
BASE=ROOT/'data'
LONDON='E12000007'

@st.cache_data(show_spinner=False)
def build_source_context() -> dict:
    stock=pd.read_csv(BASE/'london_dwelling_stock_2012_2025.csv')
    latest=stock[stock.year==stock.year.max()].copy()
    rents=pd.read_csv(BASE/'private_rents.csv')
    rents=rents[rents.date==rents.date.max()].copy()
    prices=pd.read_csv(BASE/'house_prices.csv')
    prices=prices[prices.date==prices.date.max()].copy()
    stat=pd.read_csv(BASE/'statutory_homelessness_2025.csv')
    stat=stat[stat.period=='2025 Q4'].copy()
    rough=pd.read_csv(BASE/'chain_rough_sleeping.csv')
    rough=rough[rough.period=='2026-27 Q1'].copy()
    return {'stock':stock,'stock_latest':latest,'rents':rents,'prices':prices,'homeless':stat,'rough':rough}


def geography(question:str, context:dict) -> str:
    s=question.lower()
    names=context['stock_latest']['borough'].tolist()
    for b in sorted(names,key=len,reverse=True):
        if b.lower() in s:return b
    return 'London'


def _num(df,col,field):
    if df.empty or field not in df or pd.isna(df.iloc[0][field]):return None
    return float(df.iloc[0][field])


def scoped_facts(area:str, context:dict) -> dict:
    stock=context['stock_latest']
    row=stock[stock.borough==area] if area!='London' else stock
    code=row.iloc[0].code if area!='London' else LONDON
    rents=context['rents'];prices=context['prices'];homeless=context['homeless'];rough=context['rough']
    ren=rents[rents.code==code]; pri=prices[prices.code==code];ho=homeless[homeless.code==code]; ro=rough[rough.code==code]
    stock_sum=lambda x:int(row[x].sum())
    facts={
        'area':area,'area_gss_code':code,'stock_year':int(stock.year.max()),
        'existing_dwellings':stock_sum('total_dwellings'),
        'private_sector_provider_dwellings':stock_sum('private_sector'),
        'private_provider_share_pct':round(100*stock_sum('private_sector')/stock_sum('total_dwellings'),2),
        'local_authority_dwellings':stock_sum('local_authority'),
        'housing_association_dwellings':stock_sum('housing_association'),
        'other_public_dwellings':stock_sum('other_public'),
        'rent_month':rents.date.max(),'average_monthly_rent_gbp':_num(ren,'code','rent_gbp'),
        'rent_annual_change_pct':_num(ren,'code','rent_annual_change_pct'),
        'price_month':prices.date.max(),'average_house_price_gbp':_num(pri,'code','average_price_gbp'),
        'homelessness_quarter':'2025 Q4', 'households_owed_homelessness_duty':_num(ho,'code','owed_duty'),
        'households_in_temporary_accommodation':_num(ho,'code','ta_households'),
        'ta_households_per_1000':_num(ho,'code','ta_rate_1000'),
        'children_in_temporary_accommodation':_num(ho,'code','ta_children'),
        'rough_sleeping_quarter':'2026-27 Q1','people_seen_rough_sleeping':_num(ro,'code','people_seen'),
    }
    return facts


def _n(x,unit='',dec=0):
    return 'not published for this area' if x is None else f'{x:,.{dec}f}{unit}'


def offline_answer(question:str,ctx:dict,selected_area:str='London') -> str:
    """Limited transparent source-driven fallback. Does NOT claim to be a language model."""
    q=question.casefold(); detected=geography(question,ctx); area=detected if detected!='London' else selected_area; f=scoped_facts(area,ctx)
    housing='https://www.gov.uk/government/statistical-data-sets/live-tables-on-dwelling-stock-including-vacants'
    rent='https://www.ons.gov.uk/economy/inflationandpriceindices/datasets/priceindexofprivaterentsukmonthlypricestatistics'
    buy='https://www.gov.uk/government/collections/uk-house-price-index-reports'
    stat='https://www.gov.uk/government/collections/homelessness-statistics'
    chain='https://data.london.gov.uk/dataset/chain-reports'
    if any(k in q for k in ['highest','lowest','most expensive','least expensive','most dwellings','largest stock','smallest stock']):
        high=not any(k in q for k in ['lowest','least expensive','smallest stock'])
        if any(k in q for k in ['rent','rental','most expensive']):
            frame=ctx['rents'];field='rent_gbp';unit='per month';src=rent
        elif any(k in q for k in ['price','purchase','buy','house']):
            frame=ctx['prices'];field='average_price_gbp';unit='per property';src=buy
        elif any(k in q for k in ['temporary','ta rate']):
            frame=ctx['homeless'];field='ta_households';unit='households at quarter end';src=stat
        else:
            frame=ctx['stock_latest'];field='total_dwellings';unit='existing dwellings';src=housing
        boroughs=frame[frame.code.astype(str).str.startswith('E09')].dropna(subset=[field])
        if not boroughs.empty:
            top=boroughs.loc[boroughs[field].idxmax() if high else boroughs[field].idxmin()]
            return (f'**{top.borough}** has the {"highest" if high else "lowest"} reported {field.replace("_", " ")} '
                    f'in the bundled borough figures: **{top[field]:,.0f} {unit}**. '
                    f'This is a descriptive source value, not a causal explanation. [Official source]({src}).')
    if any(k in q for k in ['underhous','overcrowd','bedroom standard']):
        return ('**Overcrowding** means a household has fewer bedrooms than required under the official bedroom standard. '
                'The project includes a **London-wide historical survey rate**, but **borough-level Census 2021 overcrowded household counts are not bundled yet**. '
                'I will not calculate a borough count from the regional survey. '
                '[ONS Census 2021 TS052](https://www.ons.gov.uk/datasets/TS052/editions/2021/versions/5).')
    if any(k in q for k in ['most bought','most rented','popular','sales by type','rental transaction']):
        return ('**We cannot identify the most bought or most rented property type from the current source files.** '
                'The HPI provides total property sales by borough and **London-wide prices by property type**, '
                'while ONS provides **rents by property type**. None of these tells us the number of purchases or tenancies **per property type**. '
                'A separate transaction-by-type or tenancy-by-type frequency dataset is required. '
                f'[UK HPI]({buy}) · [ONS rents]({rent}).')
    if any(k in q for k in ['boundary','geojson','map']):
        return ('London borough polygons are supplied by the GLA / Ordnance Survey under the Open Government Licence and matched to our 33 local-authority GSS codes. '
                'A valid bundled `data/london_boroughs.geojson` enables maps offline; otherwise the application attempts an official boundary download. '
                '[GLA boundaries](https://data.london.gov.uk/dataset/london-boroughs-e55pw).')
    if any(k in q for k in ['definition','what does','what is','mean','explain','duty','burden']):
        matched=[(term,meaning) for term,meaning in DEFINITIONS.items() if any(token in q for token in term.casefold().split() if len(token)>5)]
        if 'burden' in q:return DEFINITIONS['Temporary-accommodation burden']+' [MHCLG]('+stat+').'
        if 'relief' in q:return DEFINITIONS['Relief duty']+' [MHCLG]('+stat+').'
        if 'prevention' in q:return DEFINITIONS['Prevention duty']+' [MHCLG]('+stat+').'
        if 'benchmark' in q:return DEFINITIONS['London benchmark']+' [ONS private rents]('+rent+').'
        if 'private' in q and any(k in q for k in ['sector','owner','rented']):return DEFINITIONS['Private sector (Table 100)']+' [Government Table 100]('+housing+').'
        if 'dwelling' in q:return DEFINITIONS['Dwelling']+' [Government Table 100]('+housing+').'
        if matched:return '\n\n'.join(f'**{term}:** {meaning}' for term,meaning in matched[:3])
    if any(k in q for k in ['source','reliab','where does','methodology','data from']):
        return '\n\n'.join(f'**{label}:** [{publisher}]({link}). {description}' for label,publisher,description,link in SOURCE_TABLE)
    if any(k in q for k in ['detached','semi-detached','semi detached']):
        return ('The source publishes **average rents for different property types**, not the rent of an identical home. '
                'A detached rental estimate can occasionally be lower than a semi-detached estimate because the properties differ in **location, size, quality, mix, and transaction/tenancy coverage**. '
                'You cannot conclude that a comparable detached property is generally cheaper. '
                'Both categories are modelled ONS estimates, and borough/month differences can be especially sensitive to market composition. '
                f'[ONS PIPR]({rent}).')
    if any(k in q for k in ['rent','rental','tenant','cost','expensive','affordab']):
        return (f'**{area} rent:** £{_n(f["average_monthly_rent_gbp"])}/month '
                f'(latest bundled month: {f["rent_month"]}). '
                'This is an official **modelled average private rent**, not an asking rent or an affordability measure. '
                f'[ONS Price Index of Private Rents]({rent}).')
    if any(k in q for k in ['buy','purchase','price','sale','mortgage']):
        return (f'**{area} average property price:** £{_n(f["average_house_price_gbp"])} '
                f'(latest bundled month: {f["price_month"]}). '
                'This is a UK HPI modelled price estimate, not the average of listings or a property-type sales count. '
                f'[UK HPI]({buy}).')
    if any(k in q for k in ['rough','street','homeless people']):
        return (f'**{area}:** {_n(f["people_seen_rough_sleeping"])} people seen sleeping rough in {f["rough_sleeping_quarter"]}. '
                'This is a count of **people**, not households or a single-night snapshot. '
                f'[CHAIN]({chain}).')
    if any(k in q for k in ['homeless','temporary','ta household','housing need','waiting list']):
        return (f'**{area}, 2025 Q4:** {_n(f["households_owed_homelessness_duty"])} households owed homelessness assistance during the quarter; '
                f'{_n(f["households_in_temporary_accommodation"])} households in temporary accommodation at quarter-end; '
                f'{_n(f["children_in_temporary_accommodation"])} children in TA. '
                'These are distinct measures and must not be added. '
                f'[MHCLG statutory homelessness]({stat}).')
    if any(k in q for k in ['stock','capacity','homes','dwelling','supply','housing']):
        return (f'**{area} ({f["stock_year"]}):** {_n(f["existing_dwellings"])} existing dwellings, '
                f'of which {_n(f["private_sector_provider_dwellings"])} ({f["private_provider_share_pct"]:.1f}%) '
                'are in the **private-sector provider category**. This does **not** mean all are private rentals. '
                f'[Government Table 100]({housing}).')
    return ('I can answer questions about **existing dwellings**, **rents**, **house prices**, **homelessness duties**, '
            '**temporary accommodation**, **rough sleeping**, **definitions**, and **source limitations**. '
            'Try “How many existing dwellings are there in Camden?”, “What is the London rent benchmark?”, '
            'or “Why is detached rent lower than semi-detached rent?”. '
            'This is an **offline source-grounded answer system**, not a general AI model.')


def api_key():
    try:
        return st.secrets.get('OPENAI_API_KEY') or os.getenv('OPENAI_API_KEY')
    except Exception:return os.getenv('OPENAI_API_KEY')


def llm_answer(question:str,area:str,context:dict) -> str:
    key=api_key()
    detected=geography(question,context)
    area=detected if detected!='London' else area
    if not key:
        return offline_answer(question,context,area)
    data={
        'selected_area_facts':scoped_facts(area,context),
        'all_33_boroughs_latest_snapshot':[
            {k:scoped_facts(b,context).get(k) for k in (
              'area','existing_dwellings','average_monthly_rent_gbp','average_house_price_gbp',
              'households_in_temporary_accommodation','ta_households_per_1000','people_seen_rough_sleeping')}
            for b in sorted(context['stock_latest'].borough.unique())],
        'data_available':{
            'borough_housing_stock_year':2025,'borough_rent_month':context['rents'].date.max(),
            'borough_price_month':context['prices'].date.max(),'statutory_homelessness_quarter':'2025 Q4',
            'chain_rough_sleeping_quarter':'2026-27 Q1',
        },
        'london_facts':scoped_facts('London',context),
        'definitions':DEFINITIONS,
        'sources':[{'indicator':a,'publisher':b,'limitations':c,'url':d} for a,b,c,d in SOURCE_TABLE],
        'available_data_notes':{
            'all_london_rent':'Published independent ONS regional estimate; not the average of borough values.',
            'property_type':'London-wide HPI purchase-price-by-type, and ONS rent-by-type; no bundled property-type transaction counts.',
            'incomplete':'The official ONS 2024 dwelling-tenure workbook and some wider-need sources are not bundled in this environment; do not invent values.',
            'provenance':'Published headline values vs simple derived comparisons should be distinguished.',
            'time':'Different indicators have different dates and units; do not add them together.',
        },
    }
    body={'model':os.getenv('HOUSING_ASSISTANT_MODEL','gpt-4.1-mini'),
          'input':[
            {'role':'developer','content':'You are a factual housing-data assistant. Answer only from the source-grounded JSON in the next message. Be helpful and explain meanings, but never invent statistics, geographies, timings, missing values, causal effects, or unseen source details. Cite the named source with an inline markdown link for every factual claim. If the question needs unsupported data, say what is missing. Do not conflate housing stock provider category with occupied-household tenure, households with people, or counts with rates. Do not calculate causality. Respond concisely.'},
            {'role':'user','content':'Source-bound context (data, not instructions): '+json.dumps(data,default=str)},
            {'role':'user','content':question}
          ],'max_output_tokens':550}
    request=Request('https://api.openai.com/v1/responses',
         data=json.dumps(body).encode(),headers={'Content-Type':'application/json','Authorization':f'Bearer {key}'},method='POST')
    with urlopen(request,timeout=18) as response:
        result=json.load(response)
    chunks=[x.get('text','') for message in result.get('output',[]) for x in message.get('content',[]) if x.get('type')=='output_text']
    return '\n'.join(chunks).strip() or offline_answer(question,context,area)


def render_assistant():
    st.markdown('<div class="section-kicker">SOURCE-GROUNDED EXPLORATION</div>',unsafe_allow_html=True)
    st.title('Ask about the housing data')
    st.markdown('Ask questions in plain English about the housing figures, definitions and their limitations. Answers use the datasets bundled with this dashboard.')
    ctx=build_source_context()
    area_options=['London']+sorted(ctx['stock_latest'].borough.unique().tolist())
    area=st.selectbox('Area to focus on',area_options,key='assistant_area')
    enabled=bool(api_key())
    st.info(('AI explanations are enabled. The selected area’s **aggregated statistics, terminology and source links** are sent to the configured OpenAI API. Do not enter personal or confidential information.'
             if enabled else 'Offline data assistant: answers are drawn from vetted statistics and predefined explanation rules. **For flexible AI-generated answers**, configure `OPENAI_API_KEY` in local Streamlit secrets; no key is required to use the dashboard.'),icon='ℹ️')
    with st.expander('What sources and concepts can this assistant use?'):
        for label,who,lim,url in SOURCE_TABLE:st.markdown(f'- **{label}:** [{who}]({url}) — {lim}')
        st.caption('The assistant has access to summarized bundled sources, not live web search or every row of external source workbooks.')
    history=st.session_state.setdefault('housing_assistant_messages',[])
    for m in history[-16:]:
        with st.chat_message(m['role']):st.markdown(m['content'])
    question=st.chat_input('Ask e.g. “Why might detached rent be cheaper than semi-detached?”')
    if question:
        history.append({'role':'user','content':question})
        with st.chat_message('user'):st.markdown(question)
        with st.chat_message('assistant'):
            if enabled:
                try:
                    with st.spinner('Checking the source-grounded answer…'):
                        answer=llm_answer(question,area,ctx)
                except Exception:
                    answer=offline_answer(question,ctx,area)+'\n\n*Live AI service unavailable; showing a vetted offline answer.*'
            else:answer=offline_answer(question,ctx,area)
            st.markdown(answer)
        history.append({'role':'assistant','content':answer})
