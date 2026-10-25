"""Evidence-first landing page for testing London housing supply/need hypothesis.

A benchmark-vs-delivery comparison is evidence about the planning-delivery gap,
not observed consumer demand nor a causal estimate of price effects.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

BASE = Path(__file__).resolve().parent
DATA = BASE / "data"
SOURCE_STOCK = "https://www.gov.uk/government/statistical-data-sets/live-tables-on-dwelling-stock-including-vacants"
SOURCE_NET = "https://www.gov.uk/government/statistics/housing-supply-net-additional-dwellings-england-2024-to-2025/housing-supply-net-additional-dwellings-england-2024-to-2025"
SOURCE_NEED = "https://www.gov.uk/guidance/housing-and-economic-development-needs-assessments"
SOURCE_TA = "https://www.gov.uk/government/statistical-data-sets/live-tables-on-homelessness"
SOURCE_RENTS = "https://www.ons.gov.uk/economy/inflationandpriceindices/datasets/priceindexofprivaterentsukmonthlypricestatistics"
BLUE = "#3478bc"
PURPLE = "#7965b8"
TEAL = "#0c8988"
NAVY = "#18304f"

# Keep the on-screen choices short. Long selectbox entries used to show only
# their trailing ",000)" in the browser when the widget received focus.
# The source descriptions remain in the input CSV and below the chart.
BENCHMARK_CHOICES = {
    "Government method · 88k/year": {
        "prefix": "Government standard method",
        "bar_label": "Government standard method (2024)",
        "card_label": "Government estimate · per year",
        "plain_english": "The government's standard method estimates how many extra homes London needs each year. This is a planning estimate, not a count of applications.",
    },
    "GLA study · 66k/year": {
        "prefix": "GLA 2017 strategic housing market assessment",
        "bar_label": "GLA housing-need study (2017)",
        "card_label": "GLA estimate · per year",
        "plain_english": "This is an older estimate from the Greater London Authority's 2017 housing-need study. It uses a different approach and is not an observed 2025 figure.",
    },
    "London Plan · 52k/year": {
        "prefix": "London Plan 2021 target",
        "bar_label": "London Plan policy target (2021)",
        "card_label": "London Plan target · per year",
        "plain_english": "This is the London Plan's housing-delivery target, not a measurement of the full underlying need for housing.",
    },
}


def benchmark_record(benchmarks: pd.DataFrame, choice: str):
    """Return the official record matching a short on-screen label."""
    details = BENCHMARK_CHOICES[choice]
    matches = benchmarks.loc[benchmarks.benchmark.str.startswith(details["prefix"], na=False)]
    if len(matches) != 1:
        raise ValueError(f"Expected one benchmark for {choice!r}, got {len(matches)}")
    return matches.iloc[0], details


def compare_deliveries(net_additions: int, annual_benchmark: int) -> dict:
    """A comparable homes-per-year gap; not a cumulative housing backlog."""
    if annual_benchmark <= 0 or net_additions < 0:
        raise ValueError("Supply must be non-negative and benchmark positive")
    return {
        "additions": int(net_additions),
        "benchmark": int(annual_benchmark),
        "annual_difference": int(annual_benchmark - net_additions),
        "delivery_share": 100 * net_additions / annual_benchmark,
    }


def london_stock_series(df: pd.DataFrame) -> pd.DataFrame:
    required = {"year", "code", "total_dwellings"}
    if not required.issubset(df.columns):
        raise ValueError(f"Stock data missing: {required - set(df.columns)}")
    df = df.copy()
    df["total_dwellings"] = pd.to_numeric(df["total_dwellings"], errors="coerce")
    if df["total_dwellings"].isna().any():
        raise ValueError("Stock file includes unparseable dwelling totals")
    london = df.groupby("year", as_index=False)["total_dwellings"].sum().sort_values("year")
    london["stock_change"] = london["total_dwellings"].diff()
    return london


def borough_pressure(stock: pd.DataFrame, statutory: pd.DataFrame, period: str = "2025 Q4") -> pd.DataFrame:
    """Join on official GSS identifiers; do not impute missing local-authority returns."""
    years = sorted(stock.year.unique())
    first_year, last_year = int(years[0]), int(years[-1])
    first = stock.loc[stock.year.eq(first_year), ["code", "total_dwellings"]].rename(columns={"total_dwellings": "stock_first"})
    current = stock.loc[stock.year.eq(last_year), ["code", "borough", "total_dwellings"]].rename(columns={"total_dwellings": "stock_latest"})
    pressure = statutory.loc[
        statutory.period.eq(period) & statutory.level.eq("Borough"),
        ["code", "ta_households", "ta_rate_1000", "households_in_area_thousands"],
    ]
    joined = current.merge(first, on="code", validate="one_to_one").merge(pressure, on="code", how="left", validate="one_to_one")
    joined["stock_growth_pct"] = 100 * (joined["stock_latest"] / joined["stock_first"] - 1)
    joined["stock_growth_abs"] = joined["stock_latest"] - joined["stock_first"]
    return joined.sort_values("ta_rate_1000", ascending=False, na_position="last")


@st.cache_data(show_spinner=False)
def load_evidence():
    stock = pd.read_csv(DATA / "london_dwelling_stock_2012_2025.csv", dtype={"code": str})
    statutory = pd.read_csv(DATA / "statutory_homelessness_2025.csv", dtype={"code": str})
    rentals = pd.read_csv(DATA / "private_rents.csv", dtype={"code": str}, parse_dates=["date"])
    benchmarks = pd.read_csv(DATA / "housing_need_benchmarks.csv")
    net = pd.read_csv(DATA / "london_net_additions_verified.csv")
    if len(net) != 1 or not stock.year.max() >= 2025 or benchmarks.homes_per_year.le(0).any():
        raise ValueError("The hypothesis evidence inputs are incomplete")
    # Fail clearly rather than quietly displaying "000)" if a comma in a
    # benchmark name has made a CSV invalid.
    for short_label in BENCHMARK_CHOICES:
        benchmark_record(benchmarks, short_label)
    return stock, statutory, rentals, benchmarks, net


def comparison_chart(comparison: dict, benchmark_label: str = "Government standard method (2024)"):
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=["Homes actually added (2024–25)", benchmark_label],
        x=[comparison["additions"], comparison["benchmark"]],
        orientation="h", marker_color=[BLUE, PURPLE],
        text=[f'{comparison["additions"]:,.0f}', f'{comparison["benchmark"]:,.0f}'],
        textposition="outside", cliponaxis=False,
        hovertemplate="%{y}<br>%{x:,.0f} homes/year<extra></extra>",
    ))
    fig.update_layout(
        height=225, margin=dict(l=3, r=65, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=NAVY), showlegend=False,
        xaxis=dict(title="Number of homes per year", range=[0, max(comparison["benchmark"], comparison["additions"]) * 1.16],
                   gridcolor="#e5eaf1", tickformat=","),
        yaxis=dict(autorange="reversed", title=""),
    )
    return fig


def chart_stock(series: pd.DataFrame):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=series.year, y=series.total_dwellings,
        mode="lines+markers", line=dict(color=BLUE, width=3), marker=dict(size=6),
        fill="tozeroy", fillcolor="rgba(52,120,188,0.09)",
        hovertemplate="%{x}: %{y:,.0f} dwellings<extra></extra>",
    ))
    fig.update_layout(height=310, margin=dict(l=5, r=10, t=8, b=5),
                      xaxis=dict(title="Year (31 March)", tickmode="linear", dtick=2, gridcolor="#e7edf4"),
                      yaxis=dict(title="Existing dwellings", tickformat="~s", rangemode="tozero", gridcolor="#e7edf4"),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font=dict(color=NAVY))
    return fig


def chart_ta(statutory: pd.DataFrame):
    df = statutory[statutory.level.ne("Borough")].sort_values("period")
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df.period, y=df.ta_households, mode="lines+markers",
        line=dict(color=TEAL, width=3), marker=dict(size=8),
        hovertemplate="%{x}<br>%{y:,.0f} households<extra></extra>",
    ))
    fig.update_layout(height=310, margin=dict(l=5, r=10, t=8, b=5),
                      xaxis=dict(title="2025 quarter"),
                      yaxis=dict(title="Households in temporary accommodation", tickformat=",", rangemode="tozero", gridcolor="#e7edf4"),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font=dict(color=NAVY))
    return fig


def chart_borough(joined: pd.DataFrame, highlight: str):
    plot = joined.dropna(subset=["ta_rate_1000", "stock_growth_pct"]).copy()
    plot["highlight"] = plot["borough"].eq(highlight).map({True: "Selected borough", False: "Other borough"})
    fig = px.scatter(
        plot, x="stock_growth_pct", y="ta_rate_1000", hover_name="borough",
        color="highlight", color_discrete_map={"Selected borough": PURPLE, "Other borough": BLUE},
        size="stock_latest", size_max=19,
        custom_data=["stock_first", "stock_latest", "ta_households", "stock_growth_abs"],
        labels={"stock_growth_pct": "Growth in existing dwelling stock, 2012–2025 (%)",
                "ta_rate_1000": "TA households per 1,000 households, 2025 Q4",
                "highlight": ""},
    )
    fig.update_traces(
        hovertemplate="<b>%{hovertext}</b><br>Stock growth: %{x:.1f}%"
                      "<br>TA per 1,000 households: %{y:.1f}"
                      "<br>TA households: %{customdata[2]:,.0f}"
                      "<br>2025 dwellings: %{customdata[1]:,.0f}<extra></extra>",
        marker=dict(opacity=.77, line=dict(width=1, color="white")),
    )
    fig.update_layout(height=415, margin=dict(l=5, r=5, t=10, b=15),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font=dict(color=NAVY),
                      xaxis=dict(gridcolor="#e7edf4"), yaxis=dict(gridcolor="#e7edf4"),
                      legend=dict(orientation="h", y=1.12, x=0, title=""))
    return fig


def row_card(label, value, note):
    st.metric(label, value)
    st.caption(note)


def render_hypothesis_dashboard():
    stock, statutory, rentals, benchmarks, net = load_evidence()
    stats = london_stock_series(stock)
    first, last = stats.iloc[0], stats.iloc[-1]
    total_growth = (last.total_dwellings / first.total_dwellings - 1) * 100
    latest_stat = statutory.loc[(statutory.level.ne("Borough")) & statutory.period.eq("2025 Q4")].iloc[0]
    rentals_london = rentals.loc[rentals.code.eq("E12000007")].sort_values("date")
    latest_rent = rentals_london.iloc[-1]

    st.markdown('<div class="section-kicker">THE BIG QUESTION · START HERE</div>', unsafe_allow_html=True)
    st.title("Are we building enough homes in London?")
    st.markdown("""
    <p class="main-intro">London keeps adding homes. But is it adding them <b>fast enough</b> for the people who need them?
    That's the question we're trying to answer. We'll look at what has actually been built, what official estimates say
    is needed, and where people are feeling the pressure.</p>
    """, unsafe_allow_html=True)
    st.info("**One thing to keep in mind:** Homes built are counted from records. Homes 'needed' are estimates or policy targets. They're useful to compare, but they aren't the same thing as the number of people who asked for a home in 2025.")

    tabs = st.tabs(["01 · Are we keeping up?", "02 · Where can we see the pressure?", "03 · What about each borough?", "04 · Where do the numbers come from?"])
    with tabs[0]:
        st.subheader("How many homes did we add — and how many do we need?")
        st.markdown("**London added 32,680 homes in 2024–25.** The government's current planning method points to roughly **88,000 additional homes a year**. That's quite a gap — but let's be clear about whose estimate we're using.")
        st.markdown("**Choose the official estimate or target you'd like to compare with actual delivery:**")
        choice = st.radio(
            "Housing need comparison source",
            list(BENCHMARK_CHOICES),
            index=0,
            horizontal=True,
            key="hypothesis_benchmark_v7",
            label_visibility="collapsed",
        )
        selected_benchmark, details = benchmark_record(benchmarks, choice)
        comparison = compare_deliveries(int(net.net_additions.iloc[0]), int(selected_benchmark.homes_per_year))
        st.caption(details["plain_english"])
        c1, c2, c3 = st.columns(3)
        c1.metric("Homes London actually added · 2024–25", f'{comparison["additions"]:,}')
        c2.metric(details["card_label"], f'{comparison["benchmark"]:,}')
        c3.metric("Difference for this one year", f'{comparison["annual_difference"]:,}')
        st.plotly_chart(
            comparison_chart(comparison, details["bar_label"]),
            use_container_width=True, config={"displayModeBar": False},
        )
        if comparison["annual_difference"] > 0:
            st.markdown(
                f'**So what does that tell us?** London delivered **{comparison["delivery_share"]:.1f}%** of this '
                f'estimate or target in 2024–25 — **{comparison["annual_difference"]:,} homes short** of that number.'
            )
        else:
            st.markdown("**So what does that tell us?** London met or exceeded this particular estimate or target in 2024–25.")
        st.caption(
            f'**Where that comparison comes from:** {details["bar_label"]}. '
            f'{selected_benchmark.definition} **Important:** {selected_benchmark.caution}'
        )
        st.warning(
            "**This isn't London's total housing shortage.** It's the difference between homes added in one year "
            "and one annual estimate or target. It doesn't tell us how many households were waiting for a home. "
            "And an older policy target isn't interchangeable with today's estimate of need."
        )
        official_links = (
            f'**Check the original figures:** [Homes added (MHCLG)]({SOURCE_NET}) · '
            f'[Where this estimate or target comes from]({selected_benchmark.source_url})'
        )
        if details['prefix'] == 'Government standard method':
            official_links += f' · [How the government calculates the estimate]({SOURCE_NEED})'
        st.markdown(official_links)
        st.divider()
        st.subheader("Hang on — hasn’t London been adding homes all along?")
        c1, c2, c3 = st.columns(3)
        c1.metric("Homes that existed in 2025", f'{int(last.total_dwellings):,}')
        c2.metric("Homes that existed in 2012", f'{int(first.total_dwellings):,}')
        c3.metric("How much the stock grew", f'+{total_growth:.1f}%')
        st.plotly_chart(chart_stock(stats), use_container_width=True, config={"displayModeBar": False})
        st.caption(f'**Why that isn’t a contradiction:** London can have more homes than it used to, while still adding fewer new homes each year than official estimates say it needs. Source: [MHCLG Table 100]({SOURCE_STOCK}); recent years are provisional.')
        with st.expander("Does this prove we have fallen short year after year?"):
            st.markdown("Not yet. To say that, we would need to compare homes added and housing need over several years, using figures calculated on the **same basis**. Right now, we have one verified year of additions and several estimates from different years. Reusing the 2024 estimate for every earlier year would give the wrong impression. Also, some people who want a separate home may still be living with others because they can’t afford to move.")
    with tabs[1]:
        st.subheader("If there aren’t enough homes, where would we notice?")
        st.markdown("Here are a few clues: families in temporary accommodation and what people pay in rent. We **can’t add these numbers together** to get a total demand figure, and they don’t prove what caused the pressure.")
        c1, c2, c3 = st.columns(3)
        c1.metric("Households in temporary accommodation", f'{int(latest_stat.ta_households):,}')
        c1.caption("2025 Q4 · MHCLG · point-in-time households")
        c2.metric("Children in temporary accommodation", f'{int(latest_stat.ta_children):,}')
        c2.caption("2025 Q4 · children, not additional households")
        c3.metric("Average London private rent", f'£{int(latest_rent.rent_gbp):,}/mo')
        c3.caption(f'{latest_rent.date:%b %Y} · ONS modelled estimate')
        left, right = st.columns([1, 1])
        with left:
            st.markdown("**Temporary-accommodation households, 2025**")
            st.plotly_chart(chart_ta(statutory), use_container_width=True, config={"displayModeBar": False})
            st.caption('A quarterly series of household snapshots, not a flow of new applications. The final quarter was slightly below Q3.')
        with right:
            st.markdown("**London average private rent, 2015–2026**")
            r = rentals_london.copy()
            fig = px.line(r, x="date", y="rent_gbp", labels={"date": "Month", "rent_gbp": "Estimated monthly rent (£)"})
            fig.update_traces(line=dict(color=PURPLE, width=3), hovertemplate="%{x|%b %Y}: £%{y:,.0f}<extra></extra>")
            fig.update_layout(height=310, margin=dict(l=5, r=10, t=8, b=5),
                              paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                              font=dict(color=NAVY), yaxis=dict(gridcolor="#e7edf4"), xaxis=dict(gridcolor="#e7edf4"))
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            st.caption('These rents are in the pounds paid at the time. We haven’t adjusted them for inflation or people’s incomes, so this chart doesn’t tell us on its own whether renting became more affordable.')
        st.info('**What can we say so far?** We see a gap against the planning estimate, alongside expensive rents and many households in temporary accommodation. That makes the idea worth investigating — **but it doesn’t prove one caused the others**. To test that, we’d also need to look at income, migration, interest rates and policy changes.')
        st.markdown(f'[MHCLG homelessness tables ↗]({SOURCE_TA}) · [ONS rental statistics ↗]({SOURCE_RENTS})')
    with tabs[2]:
        st.subheader("If a borough adds more homes, does that mean less housing pressure?")
        st.markdown("Let’s put two things side by side: **how much each borough’s housing stock grew between 2012 and 2025**, and **how many households were in temporary accommodation per 1,000 households at the end of 2025**. Do the boroughs that grew the most have less pressure?")
        joined = borough_pressure(stock, statutory)
        present = joined.dropna(subset=["ta_rate_1000"])
        unavailable = joined.loc[joined.ta_rate_1000.isna(), "borough"].tolist()
        highlight = st.selectbox("Pick a borough to take a closer look", ["None"] + sorted(present.borough.tolist()), key="hypothesis_highlight")
        st.plotly_chart(chart_borough(joined, highlight), use_container_width=True, config={"displayModeBar": False})
        st.caption('Bigger bubbles mean more existing homes in 2025. Hover over a bubble for the exact numbers. This comparison can reveal patterns, but it cannot show that new homes caused a change in homelessness.')
        if highlight != "None":
            rec = present.loc[present.borough.eq(highlight)].iloc[0]
            x1, x2, x3 = st.columns(3)
            x1.metric("2012–25 stock growth", f'{rec.stock_growth_pct:+.1f}%')
            x2.metric("TA per 1,000 households", f'{rec.ta_rate_1000:.1f}')
            x3.metric("TA households · 2025 Q4", f'{int(rec.ta_households):,}')
        if unavailable:
            st.warning("We can’t show these boroughs because their temporary-accommodation figures are missing: " + ", ".join(sorted(unavailable)) + ". Missing data are not treated as zero.")
        st.info('**A striking borough case — Newham:** dwelling stock increased about **30.3%** between 2012 and 2025, yet its published 2025 Q4 temporary-accommodation rate was approximately **59.0 households per 1,000**. More dwellings do not necessarily mean that the households most in need can access suitable or affordable ones. This comparison alone does **not** show what would have happened without the added housing.')
        st.markdown('**Why might that happen?** A borough can build more homes and still have households who can’t find a place they can afford, or a home of the right size. We also don’t know what the situation would look like if those homes hadn’t been built.')
        st.markdown(f'[Stock source ↗]({SOURCE_STOCK}) · [Temporary-accommodation source ↗]({SOURCE_TA})')
    with tabs[3]:
        st.subheader("First, what do we actually mean by these terms?")
        definitions = [
            ("Existing housing stock (capacity)", "The number of existing dwellings, whether occupied or vacant. It is a stock at a point in time, not the number for sale or rent."),
            ("New housing supply (delivery)", "Net additional dwellings delivered over a period: builds and conversions and changes of use, less demolitions and other losses. Measured as homes per year."),
            ("Observed households", "Households recorded as sharing a main residence. This is not all latent housing demand: inability to afford a separate home can suppress household formation."),
            ("Estimated housing need", "An assessment of how many additional homes are required under a specified planning methodology, potentially incorporating backlog and affordability."),
            ("Unmet housing need", "Households or people who lack suitable or accessible housing; shown here by partial indicators including temporary accommodation, rough sleeping and overcrowding, with overlaps."),
            ("Housing cost vs affordability", "Rent and prices are costs; affordability requires relating costs to incomes and household circumstances."),
        ]
        for term, desc in definitions:
            with st.expander(term):
                st.write(desc)
        st.divider()
        st.subheader("Who collected these numbers — and what can they really tell us?")
        st.dataframe(pd.DataFrame([
            {"Question": "How many homes exist?", "Measure": "Total dwelling stock, 2012–25", "Publisher": "MHCLG · Table 100", "Limit": "Recent data provisional; includes vacant stock."},
            {"Question": "How much supply was added?", "Measure": "Net additions, 2024–25", "Publisher": "MHCLG · net supply release", "Limit": "One verified annual point included here; borough figures provisional."},
            {"Question": "How many should be added?", "Measure": "Annual planning need/target", "Publisher": "Government standard method / GLA", "Limit": "Modelled requirements from different methodologies and vintages."},
            {"Question": "Who is experiencing housing need?", "Measure": "Temporary accommodation & duty, 2025", "Publisher": "MHCLG · statutory homelessness", "Limit": "Partial, overlapping measures; some borough returns missing."},
            {"Question": "What are housing costs?", "Measure": "Private rent, 2015–26", "Publisher": "ONS · PIPR", "Limit": "Modelled nominal rent, not affordability or direct proof of scarcity."},
            {"Question": "Does increased supply lower costs?", "Measure": "Not yet estimated", "Publisher": "Objective 4", "Limit": "Requires causal or scenario assumptions; observed association is insufficient."},
        ]), hide_index=True, use_container_width=True)
        st.markdown('**What else would help us test the idea?** Let’s follow housing delivery and estimated need over several years, and add borough-level waiting-list data, overcrowding and incomes. To work out whether building more actually changes rents or homelessness, we’ll have to allow for other things changing at the same time.')
        st.markdown('**Could our hypothesis turn out to be wrong?** Absolutely. It may turn out that London has enough homes in total but not enough that people can afford or use, or that other factors explain much of the pressure. We should be just as interested in evidence that challenges our idea.')
        st.markdown(f'[MHCLG Table 100 ↗]({SOURCE_STOCK}) · [Net additions ↗]({SOURCE_NET}) · [Need assessment ↗]({SOURCE_NEED}) · [MHCLG homelessness ↗]({SOURCE_TA}) · [ONS rents ↗]({SOURCE_RENTS})')
    st.divider()
    st.caption('The numbers cover different periods: existing homes 2012–25; homes added 2024–25; homelessness 2025; private rents to Aug 2026. These are clues, not a claim that building more or fewer homes caused a specific change in rents. Objective 4 is where we explore that question.')
