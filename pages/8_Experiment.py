import streamlit as st
import pandas as pd

from data.downloader import load_market_data
from strategies.registry import get_strategy_names, get_strategy_config
from engine.core_backtest import run_strategy_backtest
from engine.edge_score import calculate_edge_score


st.title("Experiment Engine 2.1")
st.caption("Rankar resultat med EdgeCraft Score istället för bara Profit Factor")

strategy = st.selectbox(
    "Strategi",
    get_strategy_names()
)

markets = st.multiselect(
    "Marknader",
    ["SPY", "QQQ", "DIA", "IWM", "GLD", "TLT", "XLK", "XLF", "XLE", "EEM"],
    default=["SPY", "QQQ", "DIA"]
)

timeframes = st.multiselect(
    "Timeframes",
    ["1d", "1wk"],
    default=["1d"]
)

start = st.date_input("Startdatum", pd.to_datetime("2010-01-01"))
end = st.date_input("Slutdatum", pd.Timestamp.today())

initial_capital = st.number_input(
    "Startkapital",
    value=100000,
    step=10000
)

strategy_config = get_strategy_config(strategy)
parameter_grid = strategy_config["parameter_grid"]

st.subheader("Parametrar")

selected_parameters = {}

for param_name, values in parameter_grid.items():
    selected_parameters[param_name] = st.multiselect(
        param_name,
        values,
        default=values
    )

min_trades = st.number_input(
    "Minsta antal trades för godkänd ranking",
    value=100,
    step=25
)

run = st.button("START EXPERIMENT")

if run:
    results = []

    parameter_combinations = [{}]

    for param_name, values in selected_parameters.items():
        new_combinations = []

        for combo in parameter_combinations:
            for value in values:
                new_combo = combo.copy()
                new_combo[param_name] = value
                new_combinations.append(new_combo)

        parameter_combinations = new_combinations

    total = len(markets) * len(timeframes) * len(parameter_combinations)
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
                counter += len(parameter_combinations)
                progress.progress(min(counter / total, 1.0))
                continue

            for params in parameter_combinations:
                result = run_strategy_backtest(
                    data=data,
                    strategy_name=strategy,
                    initial_capital=initial_capital,
                    parameters=params,
                    market=market,
                    timeframe=timeframe
                )

                stats = result.stats

                edge_score = calculate_edge_score(stats)

                statistically_valid = stats["Trades"] >= min_trades

                ranking_score = edge_score if statistically_valid else 0

                row = {
                    "Strategy": strategy,
                    "Market": market,
                    "Timeframe": timeframe,
                    **params,
                    "Profit Factor": stats["Profit Factor"],
                    "Winrate": stats["Winrate"],
                    "Max Drawdown": stats["Max Drawdown"],
                    "Trades": stats["Trades"],
                    "Total Return": stats["Total Return"],
                    "Avg Trade": stats["Avg Trade"],
                    "EdgeCraft Score": edge_score,
                    "Statistiskt godkänd": statistically_valid,
                    "Ranking Score": ranking_score
                }

                results.append(row)

                counter += 1
                progress.progress(min(counter / total, 1.0))

    df = pd.DataFrame(results)

    if df.empty:
        st.warning("Inga resultat.")
    else:
        df = df.sort_values(
            by=["Ranking Score", "EdgeCraft Score", "Profit Factor"],
            ascending=False
        )

        df.insert(0, "Rank", range(1, len(df) + 1))

        st.subheader("Experiment-resultat")
        st.dataframe(df, use_container_width=True)

        st.subheader("Bästa statistiskt godkända resultat")

        approved_df = df[df["Statistiskt godkänd"] == True]

        if approved_df.empty:
            st.warning("Inga resultat hade tillräckligt många trades.")
        else:
            best = approved_df.iloc[0]

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Marknad", best["Market"])
            c2.metric("Timeframe", best["Timeframe"])
            c3.metric("EdgeCraft Score", best["EdgeCraft Score"])
            c4.metric("Profit Factor", best["Profit Factor"])

            c5, c6, c7 = st.columns(3)
            c5.metric("Winrate", f'{best["Winrate"]}%')
            c6.metric("Max DD", f'{best["Max Drawdown"]}%')
            c7.metric("Trades", int(best["Trades"]))

        st.download_button(
            "Ladda ner experiment som CSV",
            df.to_csv(index=False).encode("utf-8"),
            file_name=f"{strategy}_experiment_results.csv",
            mime="text/csv"
        )