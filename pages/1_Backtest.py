import streamlit as st
import pandas as pd

from data.downloader import load_market_data
from strategies.registry import get_strategy_names, get_strategy_config
from engine.core_backtest import run_strategy_backtest
from charts.equity import plot_equity_curve


st.title("Backtest v0.44")
st.caption("Core Architecture 1.0 – backtest via Strategy Runner")

st.sidebar.header("Backtest-inställningar")

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

parameter_values = {}

st.sidebar.subheader("Strategiparametrar")

for parameter_name, default_value in defaults.items():
    if isinstance(default_value, int):
        parameter_values[parameter_name] = st.sidebar.slider(
            parameter_name,
            min_value=1,
            max_value=300,
            value=int(default_value),
            step=1
        )

    elif isinstance(default_value, float):
        parameter_values[parameter_name] = st.sidebar.number_input(
            parameter_name,
            value=float(default_value),
            step=0.1
        )

    elif isinstance(default_value, bool):
        parameter_values[parameter_name] = st.sidebar.checkbox(
            parameter_name,
            value=bool(default_value)
        )

    elif default_value is None:
        parameter_values[parameter_name] = st.sidebar.selectbox(
            parameter_name,
            [None, "EMA100", "EMA200"]
        )

    else:
        parameter_values[parameter_name] = st.sidebar.text_input(
            parameter_name,
            value=str(default_value)
        )

run = st.sidebar.button("KÖR BACKTEST")


if run:
    data = load_market_data(
        ticker=ticker,
        start=start,
        end=end,
        interval=timeframe
    )

    if data.empty:
        st.error("Ingen data hittades.")
    else:
        result = run_strategy_backtest(
            data=data,
            strategy_name=strategy_name,
            initial_capital=initial_capital,
            parameters=parameter_values,
            market=ticker,
            timeframe=timeframe
        )

        st.session_state["last_backtest_result"] = result
        st.session_state["last_backtest_strategy"] = strategy_name
        st.session_state["last_backtest_market"] = ticker
        st.session_state["last_backtest_timeframe"] = timeframe
        st.session_state["last_backtest_parameters"] = parameter_values

        result_df = result.equity
        trades_df = result.trades
        stats = result.stats

        st.success("Backtest sparat till sessionen. Monte Carlo kan nu köras.")

        st.subheader("Resultat")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Profit Factor", stats["Profit Factor"])
        c2.metric("Winrate", f'{stats["Winrate"]}%')
        c3.metric("Max Drawdown", f'{stats["Max Drawdown"]}%')
        c4.metric("Trades", stats["Trades"])

        c5, c6 = st.columns(2)
        c5.metric("Total Return", f'{stats["Total Return"]}%')
        c6.metric("Avg Trade", f'{stats["Avg Trade"]}%')

        st.subheader("Valda parametrar")
        st.json(parameter_values)

        st.subheader("Equity Curve")

        fig = plot_equity_curve(
            result_df,
            f"{ticker} - {timeframe} - {strategy_name}"
        )

        st.pyplot(fig)

        st.subheader("Senaste trades")

        if trades_df.empty:
            st.warning("Inga trades hittades.")
        else:
            st.dataframe(
                trades_df.tail(20),
                use_container_width=True
            )

        st.download_button(
            "Ladda ner trades som CSV",
            trades_df.to_csv(index=False).encode("utf-8"),
            file_name=f"{ticker}_{strategy_name}_trades.csv",
            mime="text/csv"
        )

else:
    st.info("Välj inställningar och tryck på KÖR BACKTEST.")