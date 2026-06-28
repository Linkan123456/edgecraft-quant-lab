import streamlit as st
import pandas as pd
import itertools

from data.downloader import load_market_data
from strategies.registry import get_strategy_names, get_strategy_config
from engine.walk_forward import (
    run_walk_forward_test,
    generate_walk_forward_summary
)

from charts.walk_forward_dashboard import (
    plot_test_score_by_window,
    plot_test_return_by_window,
    plot_test_profit_factor_by_window,
    plot_test_pass_fail
)


st.title("Walk Forward v0.59")
st.caption("Out-of-sample-test + Dashboard")

st.sidebar.header("Walk Forward-inställningar")

strategy_name = st.sidebar.selectbox(
    "Strategi",
    get_strategy_names()
)

ticker = st.sidebar.selectbox(
    "Marknad",
    ["SPY", "QQQ", "DIA", "IWM", "GLD", "TLT", "XLK", "XLF", "XLE", "EEM"]
)

timeframe = st.sidebar.selectbox(
    "Timeframe",
    ["1d", "1wk"]
)

start = st.sidebar.date_input(
    "Startdatum",
    pd.to_datetime("2010-01-01")
)

end = st.sidebar.date_input(
    "Slutdatum",
    pd.Timestamp.today()
)

initial_capital = st.sidebar.number_input(
    "Startkapital",
    value=100000,
    step=10000
)

train_size = st.sidebar.number_input(
    "Train candles",
    value=500,
    step=50,
    min_value=100
)

test_size = st.sidebar.number_input(
    "Test candles",
    value=125,
    step=25,
    min_value=25
)

strategy_config = get_strategy_config(strategy_name)
parameter_grid = strategy_config["parameter_grid"]

st.sidebar.subheader("Strategiparametrar")

selected_parameters = {}

for parameter_name, parameter_values in parameter_grid.items():
    selected_parameters[parameter_name] = st.sidebar.multiselect(
        parameter_name,
        parameter_values,
        default=parameter_values
    )

run = st.sidebar.button("KÖR WALK FORWARD")


def build_parameter_combinations(selected_params):

    keys = list(selected_params.keys())
    values = list(selected_params.values())

    if any(len(v) == 0 for v in values):
        return []

    return [
        dict(zip(keys, combination))
        for combination in itertools.product(*values)
    ]


if run:

    parameter_sets = build_parameter_combinations(selected_parameters)

    if len(parameter_sets) == 0:
        st.error("Inga parameterkombinationer valda.")
        st.stop()

    data = load_market_data(
        ticker=ticker,
        start=start,
        end=end,
        interval=timeframe
    )

    if data.empty:
        st.error("Ingen data hittades.")
        st.stop()

    st.subheader("Diagnostik")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Candles", len(data))
    c2.metric("Parametrar", len(parameter_sets))
    c3.metric("Train", train_size)
    c4.metric(
        "Möjliga fönster",
        max(0, int((len(data)-train_size)/test_size))
    )

    walk_forward_df = run_walk_forward_test(
        data=data,
        strategy_name=strategy_name,
        parameter_sets=parameter_sets,
        initial_capital=initial_capital,
        train_size=train_size,
        test_size=test_size,
        market=ticker,
        timeframe=timeframe
    )

    if walk_forward_df.empty:
        st.warning("Walk Forward gav inga resultat.")
        st.stop()

    st.subheader("Walk Forward Summary")

    summary = generate_walk_forward_summary(
        walk_forward_df
    )

    st.text(summary)

    approved_df = walk_forward_df[
        walk_forward_df["Test Approved"] == True
    ].copy()

    if not approved_df.empty:

        st.subheader("Nyckeltal")

        m1, m2, m3, m4 = st.columns(4)

        m1.metric(
            "Totala fönster",
            len(walk_forward_df)
        )

        m2.metric(
            "Godkända",
            len(approved_df)
        )

        m3.metric(
            "Snitt PF",
            round(
                approved_df["Test Profit Factor"]
                .replace(999,5)
                .mean(),
                2
            )
        )

        m4.metric(
            "Snitt Trades",
            round(
                approved_df["Test Trades"].mean(),
                1
            )
        )

    st.subheader("Walk Forward Dashboard")

    r1, r2 = st.columns(2)

    with r1:
        st.pyplot(
            plot_test_score_by_window(
                walk_forward_df
            )
        )

    with r2:
        st.pyplot(
            plot_test_return_by_window(
                walk_forward_df
            )
        )

    r3, r4 = st.columns(2)

    with r3:
        st.pyplot(
            plot_test_profit_factor_by_window(
                walk_forward_df
            )
        )

    with r4:
        st.pyplot(
            plot_test_pass_fail(
                walk_forward_df
            )
        )

    st.subheader("Alla testfönster")

    st.dataframe(
        walk_forward_df,
        use_container_width=True
    )

    st.download_button(
        "Ladda ner Walk Forward CSV",
        walk_forward_df.to_csv(index=False).encode("utf-8"),
        file_name="walk_forward_results.csv",
        mime="text/csv"
    )

    st.download_button(
        "Ladda ner Walk Forward Report",
        summary.encode("utf-8"),
        file_name="walk_forward_report.txt",
        mime="text/plain"
    )

else:
    st.info("Välj parametrar och tryck på KÖR WALK FORWARD.")