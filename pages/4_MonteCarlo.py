import streamlit as st
import pandas as pd

from engine.monte_carlo import (
    run_monte_carlo_simulation,
    generate_monte_carlo_report
)


st.title("Monte Carlo v0.52")
st.caption("Robusthetsanalys + Monte Carlo Score + trafikljus")

st.sidebar.header("Monte Carlo-inställningar")

initial_capital = st.sidebar.number_input(
    "Startkapital",
    value=100000,
    step=10000
)

simulations = st.sidebar.slider(
    "Antal simuleringar",
    min_value=100,
    max_value=5000,
    value=1000,
    step=100
)

seed = st.sidebar.number_input(
    "Random Seed",
    value=42,
    step=1
)

st.subheader("Datakälla")

trades_df = None

if "last_backtest_result" in st.session_state:
    backtest_result = st.session_state["last_backtest_result"]
    trades_df = backtest_result.trades
    st.success("Trades hämtades från senaste backtest.")
else:
    st.warning("Inget backtest-resultat hittades i sessionen.")

    uploaded_file = st.file_uploader(
        "Ladda upp trades-CSV med kolumnen 'Return %'",
        type=["csv"]
    )

    if uploaded_file is not None:
        trades_df = pd.read_csv(uploaded_file)
        st.success("Trades-CSV laddad.")

if trades_df is not None:
    st.subheader("Trades")

    st.dataframe(
        trades_df,
        use_container_width=True
    )

run = st.sidebar.button("KÖR MONTE CARLO")


if run:
    if trades_df is None or trades_df.empty:
        st.error("Ingen trades-data hittades.")
        st.stop()

    if "Return %" not in trades_df.columns:
        st.error("Trades-data måste innehålla kolumnen 'Return %'.")
        st.stop()

    monte_carlo_df, summary = run_monte_carlo_simulation(
        trades_df=trades_df,
        initial_capital=initial_capital,
        simulations=simulations,
        random_seed=seed
    )

    if monte_carlo_df.empty:
        st.error("Monte Carlo kunde inte genomföras.")
        st.stop()

    report = generate_monte_carlo_report(summary)

    st.subheader("Monte Carlo Summary")

    st.text(report)

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Simuleringar",
        summary["Simulations"]
    )

    c2.metric(
        "Vinstsannolikhet",
        f'{summary["Profit Probability %"]}%'
    )

    c3.metric(
        "MC Score",
        summary["Monte Carlo Score"]
    )

    c4.metric(
        "Trafikljus",
        summary["Traffic Light"]
    )

    c5, c6, c7, c8 = st.columns(4)

    c5.metric(
        "Median Return",
        f'{summary["Median Return %"]}%'
    )

    c6.metric(
        "Worst Return",
        f'{summary["Worst Return %"]}%'
    )

    c7.metric(
        "Median DD",
        f'{summary["Median Max Drawdown %"]}%'
    )

    c8.metric(
        "Worst DD",
        f'{summary["Worst Max Drawdown %"]}%'
    )

    st.subheader("Alla simuleringar")

    st.dataframe(
        monte_carlo_df,
        use_container_width=True
    )

    st.download_button(
        "Ladda ner Monte Carlo CSV",
        monte_carlo_df.to_csv(index=False).encode("utf-8"),
        file_name="monte_carlo_results.csv",
        mime="text/csv"
    )

    st.download_button(
        "Ladda ner Monte Carlo Report",
        report.encode("utf-8"),
        file_name="monte_carlo_report.txt",
        mime="text/plain"
    )

else:
    st.info("Kör ett backtest först, eller ladda upp trades-CSV.")