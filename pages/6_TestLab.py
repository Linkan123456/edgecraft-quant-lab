import streamlit as st
import pandas as pd

from data.downloader import load_market_data
from strategies.registry import get_strategy_names, get_strategy_config
from engine.validation_engine import validate_strategy


st.title("Strategy Test Lab")
st.caption("Testa en strategi på flera marknader och timeframes")

st.sidebar.header("Test Lab")

strategy_name = st.sidebar.selectbox(
    "Strategi",
    get_strategy_names()
)

markets = st.sidebar.multiselect(
    "Marknader",
    ["SPY", "QQQ", "DIA", "IWM", "GLD", "TLT", "XLK", "XLF", "XLE", "EEM"],
    default=["SPY", "QQQ", "DIA"]
)

timeframes = st.sidebar.multiselect(
    "Timeframes",
    ["1d", "1wk"],
    default=["1d"]
)

start = st.sidebar.date_input("Startdatum", pd.to_datetime("2010-01-01"))
end = st.sidebar.date_input("Slutdatum", pd.Timestamp.today())

initial_capital = st.sidebar.number_input(
    "Startkapital",
    value=100000,
    step=10000
)

strategy_config = get_strategy_config(strategy_name)
defaults = strategy_config["default_parameters"]

ma = st.sidebar.slider("MA", 50, 300, defaults["ma_length"], 10)
entry = st.sidebar.slider("Entry", 3, 20, defaults["entry_lookback"], 1)
exit_lb = st.sidebar.slider("Exit", 3, 20, defaults["exit_lookback"], 1)

run = st.sidebar.button("KÖR TEST LAB")


if run:

    results = []

    total_tests = len(markets) * len(timeframes)
    progress = st.progress(0)
    counter = 0

    for market in markets:

        for timeframe in timeframes:

            data = load_market_data(
                ticker=market,
                start=start,
                end=end,
                interval=timeframe
            )

            if data.empty:
                counter += 1
                progress.progress(counter / total_tests)
                continue

            result = validate_strategy(
                data=data,
                strategy_name=strategy_name,
                initial_capital=initial_capital,
                parameters={
                    "ma_length": ma,
                    "entry_lookback": entry,
                    "exit_lookback": exit_lb
                },
                market=market,
                timeframe=timeframe
            )

            stats = result["backtest_result"].stats
            mc = result["monte_carlo_summary"]

            results.append({
                "Strategy": strategy_name,
                "Market": market,
                "Timeframe": timeframe,
                "Rating": result["rating"],
                "Validation Score": result["validation_score"],
                "Approved": result["approved"],
                "Profit Factor": stats["Profit Factor"],
                "Winrate": stats["Winrate"],
                "Max Drawdown": stats["Max Drawdown"],
                "Trades": stats["Trades"],
                "Total Return": stats["Total Return"],
                "MC Worst DD": mc["Worst Max Drawdown"] if mc else None,
                "MC Median Return": mc["Median Return"] if mc else None
            })

            counter += 1
            progress.progress(counter / total_tests)

    if not results:
        st.warning("Inga resultat hittades.")
    else:
        df = pd.DataFrame(results)

        df = df.sort_values(
            by=["Validation Score", "Profit Factor", "Total Return"],
            ascending=False
        )

        st.subheader("Test Lab-resultat")
        st.dataframe(df, use_container_width=True)

        st.subheader("Bästa kandidat")

        best = df.iloc[0]

        c1, c2, c3, c4 = st.columns(4)

        c1.metric("Market", best["Market"])
        c2.metric("Timeframe", best["Timeframe"])
        c3.metric("Score", f'{best["Validation Score"]}%')
        c4.metric("Profit Factor", best["Profit Factor"])

        c5, c6, c7 = st.columns(3)

        c5.metric("Winrate", f'{best["Winrate"]}%')
        c6.metric("Max DD", f'{best["Max Drawdown"]}%')
        c7.metric("Trades", int(best["Trades"]))

        st.download_button(
            "Ladda ner Test Lab som CSV",
            df.to_csv(index=False).encode("utf-8"),
            file_name=f"{strategy_name}_test_lab.csv",
            mime="text/csv"
        )

else:
    st.info("Välj strategi, marknader och timeframes. Tryck sedan på KÖR TEST LAB.")