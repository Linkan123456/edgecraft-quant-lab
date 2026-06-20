
import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import matplotlib.pyplot as plt

st.set_page_config(
    page_title="EdgeCraft Quant Lab",
    page_icon="📊",
    layout="wide"
)

st.title("EdgeCraft Quant Lab 0.1")
st.caption("Project Alpha – Double Seven")

st.markdown("""
Det här är första versionen av vårt Quant Lab.  
Målet är enkelt: testa **Double Seven** på olika marknader och timeframes.
""")

st.sidebar.header("Inställningar")

market_map = {
    "SPY – S&P 500 ETF": "SPY",
    "QQQ – Nasdaq 100 ETF": "QQQ",
    "DIA – Dow Jones ETF": "DIA",
    "IWM – Russell 2000 ETF": "IWM",
}

timeframe_map = {
    "Daily": "1d",
    "4H": "4h",
    "1H": "1h",
    "30 min": "30m",
    "15 min": "15m",
    "5 min": "5m",
}

market_label = st.sidebar.selectbox("Marknad", list(market_map.keys()))
timeframe_label = st.sidebar.selectbox("Timeframe", list(timeframe_map.keys()))
initial_capital = st.sidebar.number_input("Startkapital", value=100000, step=10000)
ma_length = st.sidebar.slider("Trendfilter MA", min_value=50, max_value=300, value=200, step=10)
entry_lookback = st.sidebar.slider("Entry-lookback", min_value=3, max_value=20, value=7, step=1)
exit_lookback = st.sidebar.slider("Exit-lookback", min_value=3, max_value=20, value=7, step=1)

run = st.sidebar.button("KÖR EXPERIMENT", type="primary")


def period_for_interval(interval: str) -> str:
    if interval in ["5m", "15m", "30m"]:
        return "60d"
    if interval in ["1h", "4h"]:
        return "730d"
    return "max"


@st.cache_data(show_spinner=False)
def load_data(ticker: str, interval: str) -> pd.DataFrame:
    df = yf.download(
        ticker,
        period=period_for_interval(interval),
        interval=interval,
        auto_adjust=False,
        progress=False,
    )

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0] for c in df.columns]

    return df.dropna()


def run_double_seven(df: pd.DataFrame, capital: float, ma_len: int, entry_lb: int, exit_lb: int):
    data = df.copy()

    data["MA"] = data["Close"].rolling(ma_len).mean()
    data["LowestClose"] = data["Close"].rolling(entry_lb).min()
    data["HighestClose"] = data["Close"].rolling(exit_lb).max()

    in_position = False
    entry_price = None
    entry_time = None
    shares = 0

    equity = capital
    equity_curve = []
    trades = []

    for i in range(len(data)):
        row = data.iloc[i]
        time = data.index[i]

        if np.isnan(row["MA"]) or np.isnan(row["LowestClose"]) or np.isnan(row["HighestClose"]):
            equity_curve.append(equity)
            continue

        close = float(row["Close"])

        buy_signal = (close > row["MA"]) and (close == row["LowestClose"]) and not in_position
        sell_signal = (close == row["HighestClose"]) and in_position

        if buy_signal:
            in_position = True
            entry_price = close
            entry_time = time
            shares = equity / close

        elif sell_signal:
            exit_price = close
            pnl = shares * (exit_price - entry_price)
            ret_pct = (exit_price / entry_price - 1) * 100
            equity += pnl

            trades.append({
                "Entry time": entry_time,
                "Exit time": time,
                "Entry": entry_price,
                "Exit": exit_price,
                "PnL": pnl,
                "Return %": ret_pct,
                "Bars held": i - data.index.get_loc(entry_time)
            })

            in_position = False
            entry_price = None
            entry_time = None
            shares = 0

        if in_position:
            equity_curve.append(shares * close)
        else:
            equity_curve.append(equity)

    trades_df = pd.DataFrame(trades)
    equity_series = pd.Series(equity_curve, index=data.index[:len(equity_curve)])

    return trades_df, equity_series


def calculate_stats(trades: pd.DataFrame, equity_curve: pd.Series, capital: float):
    if trades.empty:
        return {
            "Trades": 0,
            "Winrate": 0,
            "Profit Factor": 0,
            "Total Return": 0,
            "Max Drawdown": 0,
            "Avg Trade": 0,
            "Edge Score": 0,
        }

    wins = trades[trades["PnL"] > 0]
    losses = trades[trades["PnL"] < 0]

    gross_profit = wins["PnL"].sum()
    gross_loss = abs(losses["PnL"].sum())
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else np.nan

    winrate = len(wins) / len(trades) * 100
    total_return = (equity_curve.iloc[-1] / capital - 1) * 100

    running_max = equity_curve.cummax()
    drawdown = (equity_curve / running_max - 1) * 100
    max_dd = abs(drawdown.min())

    avg_trade = trades["Return %"].mean()

    score = 0
    score += min(profit_factor / 2.0, 1) * 35 if not np.isnan(profit_factor) else 0
    score += min(winrate / 70, 1) * 25
    score += max(0, 1 - max_dd / 30) * 25
    score += min(len(trades) / 250, 1) * 15
    score = round(score, 1)

    return {
        "Trades": len(trades),
        "Winrate": round(winrate, 2),
        "Profit Factor": round(profit_factor, 3) if not np.isnan(profit_factor) else "∞",
        "Total Return": round(total_return, 2),
        "Max Drawdown": round(max_dd, 2),
        "Avg Trade": round(avg_trade, 3),
        "Edge Score": score,
    }


if run:
    ticker = market_map[market_label]
    interval = timeframe_map[timeframe_label]

    with st.spinner("Hämtar data och kör backtest..."):
        df = load_data(ticker, interval)

        if df.empty:
            st.error("Ingen data hittades.")
            st.stop()

        trades, equity_curve = run_double_seven(
            df,
            initial_capital,
            ma_length,
            entry_lookback,
            exit_lookback
        )
        stats = calculate_stats(trades, equity_curve, initial_capital)

    st.subheader("Resultat")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Profit Factor", stats["Profit Factor"])
    col2.metric("Winrate", f'{stats["Winrate"]}%')
    col3.metric("Max Drawdown", f'{stats["Max Drawdown"]}%')
    col4.metric("Trades", stats["Trades"])

    col5, col6, col7 = st.columns(3)
    col5.metric("Total Return", f'{stats["Total Return"]}%')
    col6.metric("Avg Trade", f'{stats["Avg Trade"]}%')
    col7.metric("Edge Score", f'{stats["Edge Score"]}/100')

    st.subheader("Equity Curve")
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(equity_curve.index, equity_curve.values)
    ax.set_title(f"{ticker} – {timeframe_label} – Double Seven")
    ax.grid(True)
    st.pyplot(fig)

    st.subheader("Senaste affärer")
    if trades.empty:
        st.warning("Inga affärer hittades med dessa inställningar.")
    else:
        st.dataframe(trades.tail(20), use_container_width=True)

    csv = trades.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Ladda ner trades som CSV",
        data=csv,
        file_name=f"trades_{ticker}_{interval}.csv",
        mime="text/csv"
    )

else:
    st.info("Välj inställningar till vänster och tryck på **KÖR EXPERIMENT**.")
