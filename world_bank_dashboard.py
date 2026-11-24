# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "altair==6.3.0",
#     "marimo>=0.25.2",
#     "numpy==2.5.5",
#     "pandas==3.1.1",
#     "pingouin==0.7.0",
# ]
# ///
import marimo

__generated_with = "0.25.2"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    import altair as alt
    import numpy as np
    import pingouin as pg

    return alt, mo, np, pd, pg


@app.cell
def _(pd):
    base_url = "https://docs.google.com/spreadsheets/d/"
    doc_id = "1YY5iwL8J53umfHMNhJd1m-MbRPtRpX65oyxhq1KjzuI/"
    doc_format = "export?format=csv"

    url = base_url + doc_id + doc_format

    df_raw = pd.read_csv(url)
    return (df_raw,)


@app.cell
def _(df_raw, pd):
    # selected countries
    countries = {
        "Nigeria": "Nigeria",
        "India": "India",
        "Brazil": "Brazil",
        "Korea, Rep.": "South Korea",
        "Japan": "Japan",
        "Germany": "Germany",
    }

    df = df_raw.copy()

    # year from date
    df["year"] = pd.to_numeric(df["date"].astype(str).str.extract(r"(\d{4})", expand=False), errors="coerce")

    # countries, years 2000–2020
    df = df[df["country"].isin(countries.keys()) & df["year"].between(2000, 2020)].copy()
    df["country"] = df["country"].map(countries)

    # indicators as numbers
    for _column in [
        "birth_rate",
        "death_rate",
        "life_expectancy_at_birth",
        "individuals_using_internet%",
        "GDP_current_US",
        "population",
        "rural_population",
    ]:
        df[_column] = pd.to_numeric(df[_column], errors="coerce")

    # per person values
    _population = df["population"].where(df["population"] > 0)
    df["gdp_per_capita"] = df["GDP_current_US"] / _population
    df["rural_population%"] = df["rural_population"] / _population * 100

    df = df.sort_values(["country", "year"]).reset_index(drop=True)
    return countries, df


@app.cell
def _(alt, countries, mo):
    # colors and labels
    orange, purple = "#e66101", "#5e3c99"

    country_colors = alt.Scale(
        domain=list(countries.values()),
        range=["#b35806", orange, "#fdb863", "#b2abd2", "#8073ac", purple],
    )

    # sign = expected direction
    indicators = {
        "individuals_using_internet%": {"label": "Internet users (% of population)", "name": "internet use", "sign": -1},
        "gdp_per_capita": {"label": "GDP per capita (US$)", "name": "GDP per capita", "sign": -1},
        "rural_population%": {"label": "Rural population (% of population)", "name": "the rural share", "sign": 1},
        "life_expectancy_at_birth": {"label": "Life expectancy (years)", "name": "life expectancy", "sign": -1},
    }
    birth_label = "Birth rate (births per 1,000 people)"
    death_label = "Death rate (deaths per 1,000 people)"
    gdp_axis = alt.Axis(values=[500, 1000, 2000, 5000, 10000, 20000, 50000], format="~s")


    def small_table(table):
        return mo.md(table.to_html(index=False, border=0))

    return (
        birth_label,
        country_colors,
        death_label,
        gdp_axis,
        indicators,
        orange,
        purple,
        small_table,
    )


@app.cell
def _(mo, orange, purple):
    header = mo.md(
        f"""
    # Group 4 · “Growing internet use brings birth rates down.”
    **Members:** Rosemary Marion Ndyemanya · Eshal Subaida Nazar · Niels Löckmann

    - **Why this claim:** Falling birth rates are often blamed on screens. New studies from 2026 link smartphones to fewer births, while older studies find effects in both directions.
    - **Why these indicators:** The birth rate is what the claim is about, internet use is the claimed cause. GDP per capita, rural population and life expectancy show whether wealth, cities or simply time move just as closely with births.
    - **Why these countries:** Six countries at different stages: higher birth rates in <b style="color:{orange}">orange</b> (Nigeria, India, Brazil), low birth rates and ageing populations in <b style="color:{purple}">purple</b> (South Korea, Japan, Germany).

    *Choose an indicator and a period. Year-to-year changes remove the shared trend over time. Hover over points for details.*
    """
    )
    return (header,)


@app.cell
def _(indicators, mo):
    comparison = mo.ui.dropdown(
        options={info["label"]: column for column, info in indicators.items()},
        value=indicators["individuals_using_internet%"]["label"],
        label="Compare birth rate with",
    )
    period = mo.ui.range_slider(start=2000, stop=2020, step=1, value=[2000, 2020], label="Period")
    changes = mo.ui.switch(value=False, label="Year-to-year changes")
    return changes, comparison, period


@app.cell
def _(birth_label, changes, comparison, df, indicators, period):
    # selected values
    selected_indicator = comparison.value
    start_year, end_year = period.value

    _columns = [selected_indicator, "birth_rate"]
    _values = df[["country", "year", *_columns]].copy()
    if changes.value:
        _values[_columns] = _values.groupby("country")[_columns].diff()
    filtered_df = _values[_values["year"].between(start_year, end_year)].dropna()

    _prefix = "Yearly change: " if changes.value else ""
    x_title = _prefix + indicators[selected_indicator]["label"]
    y_title = _prefix + birth_label
    return (
        end_year,
        filtered_df,
        selected_indicator,
        start_year,
        x_title,
        y_title,
    )


@app.cell
def _(
    alt,
    changes,
    country_colors,
    filtered_df,
    gdp_axis,
    selected_indicator,
    x_title,
    y_title,
):
    _country_click = alt.selection_point(fields=["country"], bind="legend")
    _log = selected_indicator == "gdp_per_capita" and not changes.value
    _base = (
        alt.Chart(filtered_df)
        .add_params(_country_click)
        .encode(
            x=alt.X(
                f"{selected_indicator}:Q",
                title=x_title,
                scale=alt.Scale(type="log") if _log else alt.Scale(zero=False),
                axis=gdp_axis if _log else alt.Axis(),
            ),
            y=alt.Y("birth_rate:Q", title=y_title, scale=alt.Scale(zero=False)),
            color=alt.Color("country:N", scale=country_colors, title="Country"),
        )
    )
    _points = (
        _base.mark_circle(size=60, opacity=0.85)
        .transform_filter(_country_click)
        .encode(
            tooltip=[
                alt.Tooltip("country:N", title="Country"),
                alt.Tooltip("year:Q", title="Year"),
                alt.Tooltip(f"{selected_indicator}:Q", title=x_title, format=",.1f"),
                alt.Tooltip("birth_rate:Q", title=y_title, format=".1f"),
            ]
        )
    )
    # trend per country
    _trend = (
        _base.transform_filter(_country_click)
        .transform_regression(
            selected_indicator, "birth_rate", groupby=["country"], method="log" if _log else "linear"
        )
        .mark_line(strokeWidth=2)
    )

    scatter = (_points + _trend).properties(width=440, height=330)
    return (scatter,)


@app.cell
def _(
    changes,
    countries,
    end_year,
    filtered_df,
    mo,
    pd,
    pg,
    selected_indicator,
    small_table,
    start_year,
):
    # Spearman per country
    _rows, _skipped = [], []
    for _country in countries.values():
        _d = filtered_df[filtered_df["country"] == _country]
        if len(_d) < 5 or _d[selected_indicator].nunique() < 2 or _d["birth_rate"].nunique() < 2:
            _skipped.append(_country)
            continue
        _test = pg.corr(_d[selected_indicator], _d["birth_rate"], method="spearman")
        _time = pg.corr(_d["year"], _d["birth_rate"], method="spearman")
        _rows.append({
            "Country": _country,
            "n": _test["n"].iloc[0],
            "r": _test["r"].iloc[0],
            "p": _test["p_val"].iloc[0],
            "CI95": _test["CI95"].iloc[0],
            "r with year": _time["r"].iloc[0],
        })
    tests = pd.DataFrame(_rows, columns=["Country", "n", "r", "p", "CI95", "r with year"])

    # rounded for display
    _shown = tests.assign(
        r=tests["r"].map("{:.2f}".format),
        p=tests["p"].map(lambda p: "< 0.001" if p < 0.001 else f"{p:.3f}"),
        CI95=tests["CI95"].map(lambda ci: f"[{ci[0]:.2f}, {ci[1]:.2f}]"),
        **{"r with year": tests["r with year"].map("{:.2f}".format)},
    )
    if changes.value:
        _shown = _shown.drop(columns="r with year")

    _items = [mo.md(f"**Spearman, {start_year}–{end_year}**" + (" · year-to-year changes" if changes.value else ""))]
    if len(tests):
        _items.append(small_table(_shown))
    if _skipped:
        _items.append(mo.callout(mo.md(f"Not tested, fewer than 5 years or no change: {', '.join(_skipped)}."), kind="warn"))
    _note = "Spearman, because internet use grows in an S-curve, so the relationship is curved, and a few extreme years count less."
    if not changes.value:
        _note += " r with year: how closely the birth rate simply follows time."
    _items.append(mo.md(f"*{_note}*"))
    test_panel = mo.vstack(_items)
    return test_panel, tests


@app.cell
def _(
    alt,
    country_colors,
    filtered_df,
    mo,
    selected_indicator,
    x_title,
    y_title,
):
    _country_click = alt.selection_point(fields=["country"], bind="legend")

    def _histogram(column, title):
        return (
            alt.Chart(filtered_df)
            .add_params(_country_click)
            .mark_bar()
            .transform_filter(_country_click)
            .encode(
                x=alt.X(f"{column}:Q", bin=alt.Bin(maxbins=20), title=title),
                y=alt.Y("count()", title="Country-years"),
                color=alt.Color("country:N", scale=country_colors, title="Country"),
            )
            .properties(width=330, height=200)
        )


    distributions = mo.vstack([
        mo.md("*Skewed values, outliers or separate groups of countries speak for Spearman instead of Pearson.*"),
        _histogram("birth_rate", y_title) | _histogram(selected_indicator, x_title),
    ])
    return (distributions,)


@app.cell
def _(
    alt,
    birth_label,
    countries,
    country_colors,
    death_label,
    df,
    end_year,
    gdp_axis,
    indicators,
    mo,
    np,
    selected_indicator,
    small_table,
    start_year,
):
    _years = df.loc[
        df["year"].between(start_year, end_year),
        ["country", "year", "birth_rate", "death_rate", *indicators],
    ]


    def _lines(column, title, legend=True):
        _gdp = column == "gdp_per_capita"
        return (
            alt.Chart(_years)
            .mark_line(strokeWidth=2.5)
            .encode(
                x=alt.X("year:Q", title=None, axis=alt.Axis(format="d")),
                y=alt.Y(
                    f"{column}:Q",
                    title=None,
                    scale=alt.Scale(type="log") if _gdp else alt.Scale(zero=False),
                    axis=gdp_axis if _gdp else alt.Axis(),
                ),
                color=alt.Color("country:N", scale=country_colors, title="Country", legend=alt.Legend() if legend else None),
                tooltip=["country", "year", alt.Tooltip(f"{column}:Q", title=title, format=",.1f")],
            )
            .properties(width=330, height=190, title=title)
        )


    # ageing check
    ageing = (
        _years.groupby("country")[["death_rate", "life_expectancy_at_birth"]]
        .agg(lambda values: values.iloc[-1] - values.iloc[0])
        .reindex(countries.values())
        .round(1)
        .rename(columns={"death_rate": "Death rate (change)", "life_expectancy_at_birth": "Life expectancy (change)"})
        .assign(Ageing=lambda d: np.where((d.iloc[:, 0] > 0) & (d.iloc[:, 1] > 0), "yes", "no"))
        .rename_axis("Country")
        .reset_index()
    )

    over_time = mo.vstack([
        _lines("birth_rate", birth_label) | _lines(selected_indicator, indicators[selected_indicator]["label"]),
        mo.hstack(
            [
                _lines("death_rate", death_label, legend=False),
                mo.vstack([
                    mo.md(
                        "**Ageing check:** if the death rate rises although people live longer, the population is getting older. "
                        "Then births per 1,000 people fall even if women have as many children as before."
                    ),
                    small_table(ageing),
                ]),
            ],
            align="start",
        ),
    ])
    return (over_time,)


@app.cell
def _(changes, indicators, mo, np, purple, selected_indicator, tests):
    _n = len(tests)
    if _n == 0:
        verdict = mo.callout(mo.md("Choose a period of at least five years to get a verdict."), kind="warn")
    else:
        _info = indicators[selected_indicator]
        _expected = np.sign(tests["r"]) == _info["sign"]
        _significant = tests["p"] < 0.05
        _hits, _sig_hits = _expected.sum(), (_expected & _significant).sum()
        _against = (~_expected & _significant).sum()
        _median = tests["r"].abs().median()
        _strength = "negligible" if _median < 0.1 else "small" if _median < 0.3 else "moderate" if _median < 0.5 else "large"
        _time = (tests["r with year"].abs().round(2) >= tests["r"].abs().round(2)).sum()
        _claim = "the claim" if selected_indicator == "individuals_using_internet%" else f"a link with {_info['name']}"

        # verdict rules
        if _sig_hits > _n / 2 and (changes.value or _time <= _n / 2):
            _word = f"supports {_claim}"
        elif _sig_hits > _n / 2:
            _word = f"cannot tell: time alone correlates at least as strongly in {_time} of {_n} countries"
        elif _against > _n / 2:
            _word = f"contradicts {_claim}"
        elif _sig_hits + _against <= _n / 2:
            _word = "cannot tell: most correlations are not significant"
        else:
            _word = "gives a mixed picture"

        _sign = "negative" if _info["sign"] < 0 else "positive"
        _limit = (
            "Shared trends are removed here, but a correlation still cannot show cause and effect: a third factor such as income can move both."
            if changes.value
            else "A correlation cannot show cause and effect: rising wealth can drive both, and in ageing countries the birth rate also falls because there are fewer young people."
        )
        verdict = mo.md(
            f"In **{_hits} of {_n}** countries the correlation is {_sign} as expected, **{_sig_hits}** of them significant (p < 0.05). "
            f"The typical strength is {_strength} (median |r| = {_median:.2f}). **Verdict: the data {_word}.** {_limit}"
        ).style({"border-left": f"4px solid {purple}", "padding": "0.2rem 1rem"})
    return (verdict,)


@app.cell
def _(
    changes,
    comparison,
    distributions,
    end_year,
    header,
    mo,
    over_time,
    period,
    scatter,
    start_year,
    test_panel,
    verdict,
):
    mo.vstack([
        header,
        mo.hstack([comparison, period, mo.md(f"**{start_year}–{end_year}**"), changes], justify="start", gap=2),
        mo.ui.tabs({
            "Claim check": mo.vstack([mo.hstack([scatter, test_panel], align="start"), verdict]),
            "Over time": over_time,
            "Distributions": distributions,
        }),
    ])
    return


if __name__ == "__main__":
    app.run()
