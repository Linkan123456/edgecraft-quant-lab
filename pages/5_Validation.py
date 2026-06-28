import streamlit as st
import pandas as pd

from data.downloader import load_market_data
from strategies.registry import get_strategy_names, get_strategy_config
from engine.validation_engine import validate_strategy


st.title("Strategy Validation")
st.caption("EdgeCraft Validation Standard (EVS) 1.0")

st.sidebar.header("Validation")

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

strategy_config = get_strategy_config(strategy_name)
defaults = strategy_config["default_parameters"]

ma = st.sidebar.slider(
    "MA",
    50,
    300,
    defaults["ma_length"],
    10
)

entry = st.sidebar.slider(
    "Entry",
    3,
    20,
    defaults["entry_lookback"],
    1
)

exit_lb = st.sidebar.slider(
    "Exit",
    3,
    20,
    defaults["exit_lookback"],
    1
)

run = st.sidebar.button("VALIDERA STRATEGI")

if run:

    data = load_market_data(
        ticker=ticker,
        start=start,
        end=end,
        interval=timeframe
    )

    result = validate_strategy(
        data=data,
        strategy_name=strategy_name,
        initial_capital=initial_capital,
        parameters={
            "ma_length": ma,
            "entry_lookback": entry,
            "exit_lookback": exit_lb
        },
        market=ticker,
        timeframe=timeframe
    )

    st.header(result["rating"])

    st.metric(
        "Validation Score",
        f'{result["validation_score"]}%'
    )

    st.subheader("Kontroller")

    checks = result["checks"]

    for check, passed in checks.items():

        if passed:
            st.success(f"✅ {check}")
        else:
            st.error(f"❌ {check}")

    st.subheader("Backtest")

    stats = result["backtest_result"].stats

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Profit Factor",
        stats["Profit Factor"]
    )

    c2.metric(
        "Winrate",
        f'{stats["Winrate"]}%'
    )

    c3.metric(
        "Max DD",
        f'{stats["Max Drawdown"]}%'
    )

    c4.metric(
        "Trades",
        stats["Trades"]
    )

    st.subheader("Monte Carlo")

    mc = result["monte_carlo_summary"]

    if mc:

        c5, c6, c7 = st.columns(3)

        c5.metric(
            "Median Return",
            f'{mc["Median Return"]}%'
        )

        c6.metric(
            "Worst Return",
            f'{mc["Worst Return"]}%'
        )

        c7.metric(
            "Worst DD",
            f'{mc["Worst Max Drawdown"]}%'
        )

else:

    st.info(
        "Välj inställningar och klicka på VALIDERA STRATEGI."
    )