import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="EdgeCraft Quant Lab", layout="wide")

st.title("EdgeCraft Quant Lab 0.4")
st.caption("Research Mode – Double Seven")

st.sidebar.header("Research-inställningar")

markets = st.sidebar.multiselect(
    "Marknader",
    ["SPY", "QQQ", "DIA", "IWM", "GLD", "TLT", "XLK", "XLF", "XLE", "EEM"],
    default=["SPY", "QQQ", "DIA", "IWM"]
)

timeframes = st.sidebar.multiselect(
    "Timeframes",
    ["1d", "1wk"],
    default=["1d"]
)

start = st.sidebar.date_input("Startdatum", pd.to_datetime("2010-01-01"))
end = st.sidebar.date_input("Slutdatum", pd.Timestamp.today())

ma_length = st.sidebar.slider("MA", 50, 300, 200, 10)
entry_lookback = st.sidebar.slider("Entry-lookback", 3, 20, 7, 1)
exit_lookback = st.sidebar.slider("Exit-lookback", 3, 20, 7, 1)

initial_capital = st.sidebar.number_input("Startkapital", value=100000, step=10000)

run = st.sidebar.button("🚀 START RESEARCH")


def backtest_double_seven(data, initial_capital, ma_length, entry_lookback, exit_lookback):
    df = data.copy()

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df["MA"] = df["Close"].rolling(ma_length).mean()
    df["LowestClose"] = df["Close"].rolling(entry_lookback).min()
    df["HighestClose"] = df["Close"].rolling(exit_lookback).max()

    cash = initial_capital
    position = 0
    entry_price = 0
    equity_curve = []
    trades = []

    for i in range(len(df)):
        row = df.iloc[i]
        close = row["Close"]

        if np.isnan(row["MA"]):
            equity_curve.append(cash + position * close)
            continue

        equity_curve.append(cash + position * close)

        buy_signal = position == 0 and close > row["MA"] and close == row["LowestClose"]
        sell_signal = position > 0 and close == row["HighestClose"]

        if buy_signal:
            position = cash / close
            entry_price = close
            cash = 0

        elif sell_signal:
            cash = position * close
            pnl = cash - position * entry_price
            trades.append(pnl)
            position = 0
            entry_price = 0

    equity = pd.Series(equity_curve, index=df.index)
    trades = pd.Series(trades)

    if trades.empty:
        return None

    wins = trades[trades > 0]
    losses = trades[trades < 0]

    gross_profit = wins.sum()
    gross_loss = abs(losses.sum())
    pf = gross_profit / gross_loss if gross_loss > 0 else 999

    winrate = len(wins) / len(trades) * 100

    running_max = equity.cummax()
    drawdown = (equity / running_max - 1) * 100
    max_dd = abs(drawdown.min())

    total_return = (equity.iloc[-1] / initial_capital - 1) * 100

    edge_score = 0
    edge_score += min(pf / 2, 1) * 35
    edge_score += min(winrate / 75, 1) * 25
    edge_score += max(0, 1 - max_dd / 30) * 25
    edge_score += min(len(trades) / 250, 1) * 15

    return {
        "PF": round(pf, 3),
        "Winrate %": round(winrate, 2),
        "Max DD %": round(max_dd, 2),
        "Trades": len(trades),
        "Total Return %": round(total_return, 2),
        "Edge Score": round(edge_score, 1),
        "Equity": equity
    }


if run:
    results = []

    progress = st.progress(0)
    total_tests = len(markets) * len(timeframes)
    test_count = 0

    for market in markets:
        for tf in timeframes:
            test_count += 1
            progress.progress(test_count / total_tests)

            data = yf.download(
                market,
                start=start,
                end=end,
                interval=tf,
                auto_adjust=True,
                progress=False
            )

            if data.empty:
                continue

            stats = backtest_double_seven(
                data,
                initial_capital,
                ma_length,
                entry_lookback,
                exit_lookback
            )

            if stats is None:
                continue

            results.append({
                "Market": market,
                "Timeframe": tf,
                "MA": ma_length,
                "Entry": entry_lookback,
                "Exit": exit_lookback,
                "PF": stats["PF"],
                "Winrate %": stats["Winrate %"],
                "Max DD %": stats["Max DD %"],
                "Trades": stats["Trades"],
                "Total Return %": stats["Total Return %"],
                "Edge Score": stats["Edge Score"]
            })

    if not results:
        st.warning("Inga resultat hittades.")
    else:
        df_results = pd.DataFrame(results)
        df_results = df_results.sort_values(["Edge Score", "PF"], ascending=False)

        best = df_results.iloc[0]

        st.success(
            f"🏆 Bästa setup: {best['Market']} | {best['Timeframe']} | "
            f"PF {best['PF']} | Winrate {best['Winrate %']}% | "
            f"DD {best['Max DD %']}% | Score {best['Edge Score']}/100"
        )

        st.subheader("Ranking")
        st.dataframe(df_results, use_container_width=True)

        st.subheader("Topp 10")
        st.table(df_results.head(10))

        st.download_button(
            "Ladda ner resultat som CSV",
            df_results.to_csv(index=False).encode("utf-8"),
            file_name="research_results.csv",
            mime="text/csv"
        )

else:
    st.info("Välj marknader och timeframes. Tryck sedan på START RESEARCH.")