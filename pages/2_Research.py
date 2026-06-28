import itertools
import re

import pandas as pd
import streamlit as st

from charts.research_dashboard import (
    plot_drawdown_distribution,
    plot_edgecraft_distribution,
    plot_profit_factor_distribution,
    plot_return_distribution,
)
from data.downloader import load_market_data
from engine.ai_research_engine import run_filter_lab
from engine.core_backtest import run_strategy_backtest
from engine.research_engine import generate_research_report
from engine.robustness import run_robustness_analysis
from engine.scoring import calculate_edgecraft_score
from strategies.registry import get_strategy_config, get_strategy_names


st.title("Research Lab v2.0")
st.caption("Parameter Sweep + AI Research Engine + Filter Lab + Robustness Analyzer")


# ==========================================================
# Helpers
# ==========================================================


def build_parameter_combinations(selected_params):
    keys = list(selected_params.keys())
    values = list(selected_params.values())

    if any(len(v) == 0 for v in values):
        return []

    return [
        dict(zip(keys, combination))
        for combination in itertools.product(*values)
    ]


def parse_symbols(text):
    raw = re.split(r"[,;\n\s]+", text or "")
    symbols = [x.strip().upper().replace(".", "-") for x in raw if x.strip()]
    return list(dict.fromkeys(symbols))


def safe_float(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return default


def format_percent(value):
    try:
        return f"{float(value):.2f}%"
    except Exception:
        return "-"


def get_best_parameters(best_row, parameter_grid):
    params = {}
    for key in parameter_grid.keys():
        if key in best_row.index:
            value = best_row[key]
            if hasattr(value, "item"):
                value = value.item()
            params[key] = value
    return params


def show_trade_recipe(recipe, best_row=None):
    st.markdown("### HANDLA SÅ HÄR")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Strategi", recipe.get("Strategy", "-"))
    c2.metric("Timeframe", recipe.get("Timeframe", "Daily"))
    c3.metric("Entry", recipe.get("Entry", "-"))
    c4.metric("Trend", recipe.get("Trend", "-"))

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Stop", recipe.get("Stop", "-"))
    c6.metric("ATR", recipe.get("ATR Multiple", "-"))
    c7.metric("Exit", recipe.get("Exit", "-"))
    c8.metric("HH-filter", recipe.get("HH Filter", "-"))

    filters = recipe.get("Recommended Filters") or []
    if filters:
        st.success("Rekommenderade extra filter: " + ", ".join(filters))
    else:
        st.info("Inga extra filter förbättrade strategin tydligt i detta test.")

    if best_row is not None:
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("PF", round(safe_float(best_row.get("Profit Factor")), 3))
        m2.metric("Winrate", format_percent(best_row.get("Winrate", 0)))
        m3.metric("Max DD", format_percent(best_row.get("Max Drawdown", 0)))
        m4.metric("Trades", int(safe_float(best_row.get("Trades", 0))))
        m5.metric("Score", round(safe_float(best_row.get("EdgeCraft Score", 0)), 2))


# ==========================================================
# Sidebar
# ==========================================================

st.sidebar.header("Research-inställningar")

strategy_name = st.sidebar.selectbox(
    "Strategi",
    get_strategy_names(),
)

ticker = st.sidebar.selectbox(
    "Marknad för vanlig Research",
    ["SPY", "QQQ", "DIA", "IWM", "GLD", "TLT", "XLK", "XLF", "XLE", "EEM", "AAPL", "MSFT", "NVDA", "AMD", "META", "GOOG", "AMZN"],
)

timeframe = st.sidebar.selectbox(
    "Timeframe",
    ["1d", "1wk"],
)

start = st.sidebar.date_input(
    "Startdatum",
    pd.to_datetime("2010-01-01"),
)

end = st.sidebar.date_input(
    "Slutdatum",
    pd.Timestamp.today(),
)

initial_capital = st.sidebar.number_input(
    "Startkapital",
    value=100000,
    step=10000,
)

min_trades = st.sidebar.number_input(
    "Minsta antal trades",
    value=50,
    step=10,
)

near_best_ratio = st.sidebar.slider(
    "Near-best nivå",
    min_value=0.50,
    max_value=0.95,
    value=0.80,
    step=0.05,
)

st.sidebar.markdown("---")
st.sidebar.subheader("AI Research Engine")

ai_markets_text = st.sidebar.text_area(
    "Marknader för Filter Lab",
    value="AAPL, MSFT, NVDA, AMD, META, GOOG, AMZN",
    help="EdgeCraft testar professionella filter över dessa marknader.",
)

max_filters = st.sidebar.number_input(
    "Max filter att testa",
    min_value=1,
    max_value=50,
    value=14,
    step=1,
)

strategy_config = get_strategy_config(strategy_name)
parameter_grid = strategy_config["parameter_grid"]

st.sidebar.markdown("---")
st.sidebar.subheader("Strategiparametrar")

selected_parameters = {}

for parameter_name, parameter_values in parameter_grid.items():
    selected_parameters[parameter_name] = st.sidebar.multiselect(
        parameter_name,
        parameter_values,
        default=parameter_values,
    )

run_research = st.sidebar.button("KÖR RESEARCH", use_container_width=True)
run_improve = st.sidebar.button("🔬 IMPROVE STRATEGY", type="primary", use_container_width=True)


# ==========================================================
# Main
# ==========================================================

if not run_research and not run_improve:
    st.info("Välj parametrar och tryck på KÖR RESEARCH eller 🔬 IMPROVE STRATEGY.")
    st.stop()

parameter_combinations = build_parameter_combinations(selected_parameters)

if len(parameter_combinations) == 0:
    st.error("Inga parameterkombinationer valda.")
    st.stop()

with st.spinner("Kör parameter research..."):
    data = load_market_data(
        ticker=ticker,
        start=start,
        end=end,
        interval=timeframe,
    )

if data is None or data.empty:
    st.error("Ingen data hittades.")
    st.stop()

results = []
progress = st.progress(0)

for i, parameters in enumerate(parameter_combinations):
    try:
        result = run_strategy_backtest(
            data=data,
            strategy_name=strategy_name,
            initial_capital=initial_capital,
            parameters=parameters,
            market=ticker,
            timeframe=timeframe,
        )

        stats = result.stats

        edgecraft_score = calculate_edgecraft_score(
            stats,
            min_trades=min_trades,
        )

        row = {
            "Strategy": strategy_name,
            "Market": ticker,
            "Timeframe": timeframe,
            "Profit Factor": stats.get("Profit Factor", 0),
            "Winrate": stats.get("Winrate", 0),
            "Win Rate": stats.get("Winrate", 0),
            "Max Drawdown": stats.get("Max Drawdown", 0),
            "Trades": stats.get("Trades", 0),
            "Total Return": stats.get("Total Return", 0),
            "CAGR": stats.get("Total Return", 0),
            "Avg Trade": stats.get("Avg Trade", 0),
            "EdgeCraft Score": edgecraft_score,
            "Godkänd": stats.get("Trades", 0) >= min_trades,
            "Error": "",
        }

        row.update(parameters)
        results.append(row)
    except Exception as exc:
        error_row = {
            "Strategy": strategy_name,
            "Market": ticker,
            "Timeframe": timeframe,
            "Profit Factor": 0,
            "Winrate": 0,
            "Win Rate": 0,
            "Max Drawdown": 0,
            "Trades": 0,
            "Total Return": 0,
            "CAGR": 0,
            "Avg Trade": 0,
            "EdgeCraft Score": 0,
            "Godkänd": False,
            "Error": str(exc),
        }
        error_row.update(parameters)
        results.append(error_row)

    progress.progress((i + 1) / len(parameter_combinations))

research_df = pd.DataFrame(results)

approved_df = research_df[research_df["Godkänd"] == True].copy()

st.subheader("Research-resultat")

if approved_df.empty:
    st.warning("Ingen parameterkombination klarade filtret.")
    st.dataframe(research_df, use_container_width=True)
    st.stop()

approved_df = approved_df.sort_values(
    by=["EdgeCraft Score", "Profit Factor", "Total Return"],
    ascending=False,
).reset_index(drop=True)

best = approved_df.iloc[0]
best_parameters = get_best_parameters(best, parameter_grid)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Bästa Score", round(safe_float(best["EdgeCraft Score"]), 2))
c2.metric("Profit Factor", round(safe_float(best["Profit Factor"]), 3))
c3.metric("Total Return", format_percent(best["Total Return"]))
c4.metric("Trades", int(safe_float(best["Trades"])))

st.dataframe(approved_df, use_container_width=True)

# ==========================================================
# AI Research Engine / Filter Lab
# ==========================================================

if run_improve:
    st.markdown("---")
    st.header("🔬 AI Research Engine")

    ai_markets = parse_symbols(ai_markets_text)

    if not ai_markets:
        st.error("Inga marknader valda för Filter Lab.")
        st.stop()

    st.info(
        f"Utgångspunkt: bästa hittade basstrategi på {ticker}. "
        f"Filter Lab testar därefter {len(ai_markets)} marknader och upp till {max_filters} professionella filter."
    )

    with st.spinner("EdgeCraft testar professionella filter..."):
        lab_output = run_filter_lab(
            strategy_name=strategy_name,
            base_parameters=best_parameters,
            markets=ai_markets,
            timeframe=timeframe,
            start=str(start),
            end=str(end),
            initial_capital=initial_capital,
            min_trades=min_trades,
            max_filters=int(max_filters),
        )

    if lab_output.get("status") != "OK":
        st.error("AI Research Engine fick inga användbara resultat.")
        if lab_output.get("errors"):
            st.dataframe(pd.DataFrame(lab_output["errors"]), use_container_width=True)
        st.stop()

    summary_df = pd.DataFrame(lab_output.get("summary", []))
    improvements = lab_output.get("improvements", [])
    declines = lab_output.get("declines", [])
    recipe = lab_output.get("best_recipe", {})

    st.subheader("Slutsats")

    s1, s2, s3 = st.columns(3)
    s1.metric("Testade filter", len(summary_df))
    s2.metric("Förbättrade", len(improvements))
    s3.metric("Försämrade", len(declines))

    if improvements:
        st.success("Filter som förbättrade strategin:")
        st.dataframe(
            pd.DataFrame(improvements)[
                ["Filter", "Category", "Median Score", "Median PF", "Median DD", "Score Delta", "PF Delta", "DD Delta", "Approved"]
            ],
            use_container_width=True,
        )
    else:
        st.info("Inga filter förbättrade strategin tydligt i detta test.")

    if declines:
        st.warning("Filter som försämrade strategin:")
        st.dataframe(
            pd.DataFrame(declines)[
                ["Filter", "Category", "Median Score", "Median PF", "Median DD", "Score Delta", "PF Delta", "DD Delta", "Approved"]
            ],
            use_container_width=True,
        )

    show_trade_recipe(recipe, best)

    with st.expander("Alla Filter Lab-resultat", expanded=False):
        st.dataframe(summary_df, use_container_width=True)

    with st.expander("Detaljerade filtertester", expanded=False):
        st.dataframe(pd.DataFrame(lab_output.get("results", [])), use_container_width=True)

    if lab_output.get("errors"):
        with st.expander("Fel/ej testbara", expanded=False):
            st.dataframe(pd.DataFrame(lab_output.get("errors", [])), use_container_width=True)

# ==========================================================
# Classic Research Output
# ==========================================================

st.markdown("---")
st.subheader("Research Dashboard")

d1, d2 = st.columns(2)

with d1:
    st.pyplot(plot_profit_factor_distribution(approved_df))

with d2:
    st.pyplot(plot_edgecraft_distribution(approved_df))

d3, d4 = st.columns(2)

with d3:
    st.pyplot(plot_return_distribution(approved_df))

with d4:
    st.pyplot(plot_drawdown_distribution(approved_df))

st.subheader("AI Research Report")

report = generate_research_report(approved_df)
st.text(report)

st.subheader("Robustness Analyzer")

robustness_df, robustness_report = run_robustness_analysis(
    research_df=approved_df,
    score_column="EdgeCraft Score",
    min_score_ratio=near_best_ratio,
)

st.text(robustness_report)

if not robustness_df.empty:
    st.dataframe(robustness_df, use_container_width=True)

st.download_button(
    "Ladda ner Research",
    approved_df.to_csv(index=False).encode("utf-8"),
    file_name="research_results.csv",
    mime="text/csv",
)

st.download_button(
    "Ladda ner AI Report",
    report.encode("utf-8"),
    file_name="research_report.txt",
    mime="text/plain",
)

st.download_button(
    "Ladda ner Robustness Report",
    robustness_report.encode("utf-8"),
    file_name="robustness_report.txt",
    mime="text/plain",
)
