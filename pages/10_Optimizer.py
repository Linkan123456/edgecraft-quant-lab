import streamlit as st
import pandas as pd

from strategies.registry import get_strategy_names
from engine.market_timeframe_optimizer import DEFAULT_MARKETS, DEFAULT_TIMEFRAMES
from engine.optimization_pipeline import run_full_optimization_pipeline


st.set_page_config(
    page_title="EdgeCraft One-Click Optimizer",
    layout="wide",
)


# ==========================================================
# Market universe helpers
# ==========================================================

CORE_MARKETS = DEFAULT_MARKETS

NASDAQ_100_FALLBACK = [
    "AAPL", "MSFT", "NVDA", "AMZN", "META", "AVGO", "GOOGL", "GOOG", "TSLA", "COST",
    "NFLX", "AMD", "PEP", "ADBE", "LIN", "CSCO", "TMUS", "INTU", "QCOM", "AMAT",
    "TXN", "AMGN", "ISRG", "HON", "BKNG", "CMCSA", "VRTX", "PANW", "ADP", "LRCX",
    "GILD", "MU", "ADI", "MELI", "SBUX", "KLAC", "MDLZ", "REGN", "SNPS", "CDNS",
    "CRWD", "MAR", "CTAS", "ORLY", "CSX", "PYPL", "CEG", "NXPI", "MRVL", "ROP",
    "MNST", "FTNT", "ADSK", "WDAY", "ABNB", "PCAR", "PAYX", "DASH", "TEAM", "AEP",
    "ROST", "KDP", "CHTR", "EXC", "ODFL", "FAST", "DDOG", "KHC", "IDXX", "VRSK",
    "EA", "BKR", "XEL", "TTWO", "CTSH", "GEHC", "FANG", "CCEP", "ZS", "ANSS",
    "ON", "BIIB", "DXCM", "CDW", "GFS", "MDB", "ILMN", "WBD", "MRNA", "DLTR",
    "ARM", "LULU", "MCHP", "WBA", "SIRI", "TTD", "SMCI", "AZN", "PDD", "ASML",
]

SP500_FALLBACK = [
    "AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL", "GOOG", "BRK-B", "LLY", "AVGO",
    "JPM", "TSLA", "XOM", "UNH", "V", "PG", "MA", "COST", "HD", "JNJ",
    "ABBV", "WMT", "NFLX", "BAC", "KO", "MRK", "CVX", "CRM", "AMD", "PEP",
    "ADBE", "LIN", "TMO", "ORCL", "MCD", "CSCO", "ACN", "ABT", "WFC", "QCOM",
    "GE", "IBM", "TXN", "INTU", "AMAT", "CAT", "PM", "DHR", "VZ", "NOW",
    "ISRG", "NEE", "RTX", "UBER", "PFE", "UNP", "LOW", "SPGI", "GS", "HON",
    "AXP", "AMGN", "BLK", "BKNG", "T", "TJX", "SYK", "ELV", "C", "PGR",
    "ETN", "BSX", "LRCX", "VRTX", "MDT", "PANW", "ADP", "CB", "GILD", "DE",
    "ADI", "MMC", "PLD", "COP", "MU", "SBUX", "KLAC", "REGN", "AMT", "MDLZ",
    "SO", "FI", "NKE", "CI", "SCHW", "UPS", "DUK", "EQIX", "ICE", "MO",
    "CME", "SHW", "ZTS", "CL", "CMG", "BA", "APH", "WM", "MCO", "SNPS",
    "CDNS", "GD", "MCK", "PYPL", "PH", "TDG", "WELL", "CTAS", "USB", "MMM",
]


@st.cache_data(ttl=60 * 60 * 24)
def load_sp500_symbols():
    try:
        tables = pd.read_html("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies")
        df = tables[0]
        symbols = df["Symbol"].astype(str).str.replace(".", "-", regex=False).tolist()
        return sorted(list(dict.fromkeys(symbols)))
    except Exception:
        return SP500_FALLBACK


@st.cache_data(ttl=60 * 60 * 24)
def load_nasdaq100_symbols():
    try:
        tables = pd.read_html("https://en.wikipedia.org/wiki/Nasdaq-100")
        for df in tables:
            columns = [str(c).lower() for c in df.columns]
            if "ticker" in columns:
                col = df.columns[columns.index("ticker")]
                symbols = df[col].astype(str).str.replace(".", "-", regex=False).tolist()
                return sorted(list(dict.fromkeys(symbols)))
            if "symbol" in columns:
                col = df.columns[columns.index("symbol")]
                symbols = df[col].astype(str).str.replace(".", "-", regex=False).tolist()
                return sorted(list(dict.fromkeys(symbols)))
    except Exception:
        pass

    return NASDAQ_100_FALLBACK


def parse_custom_symbols(text):
    raw = text.replace("\n", ",").replace(";", ",").split(",")
    symbols = [x.strip().upper().replace(".", "-") for x in raw if x.strip()]
    return list(dict.fromkeys(symbols))


def get_market_universe(universe_name, custom_symbols, max_symbols):
    if universe_name == "Core 5":
        symbols = CORE_MARKETS
    elif universe_name == "Nasdaq 100":
        symbols = load_nasdaq100_symbols()
    elif universe_name == "S&P 500":
        symbols = load_sp500_symbols()
    else:
        symbols = parse_custom_symbols(custom_symbols)

    if max_symbols and max_symbols > 0:
        symbols = symbols[: int(max_symbols)]

    return symbols


# ==========================================================
# Formatting helpers
# ==========================================================

def get_value(data, keys, default=None):
    if not isinstance(data, dict):
        return default

    for key in keys:
        value = data.get(key)
        if value is not None:
            return value

    return default


def format_percent(value):
    try:
        return f"{float(value):.2f}%"
    except Exception:
        return "-"


def format_number(value):
    try:
        return f"{float(value):.2f}"
    except Exception:
        return "-"


def format_plain(value):
    if value is None:
        return "-"
    try:
        if isinstance(value, float):
            return f"{value:.2f}"
    except Exception:
        pass
    return str(value)


def as_df(records):
    if not records:
        return pd.DataFrame()
    return pd.DataFrame(records)


def best_exit_candidate(output, fallback_best):
    exit_df = as_df(get_value(output, ["exit_results"], []))

    if not exit_df.empty and "EdgeCraft Score" in exit_df.columns:
        exit_df = exit_df.sort_values(
            by=["EdgeCraft Score", "Profit Factor", "Total Return"],
            ascending=False,
        ).reset_index(drop=True)
        return exit_df.iloc[0].to_dict()

    return fallback_best or {}


def light_from_text(text):
    if not isinstance(text, str):
        return "⚪ Saknas"

    upper = text.upper()

    if "GRÖN" in upper:
        return "🟢 Grön"
    if "GUL" in upper:
        return "🟡 Gul"
    if "RÖD" in upper:
        return "🔴 Röd"

    return "⚪ Saknas"


def light_from_bool(value):
    return "🟢 Grön" if value else "🔴 Röd"


def light_from_score(score, green=70, yellow=50):
    try:
        score = float(score)
    except Exception:
        return "⚪ Saknas"

    if score >= green:
        return "🟢 Grön"
    if score >= yellow:
        return "🟡 Gul"
    return "🔴 Röd"


def build_human_assessment(conclusion, best, robustness_report, walk_forward_report, monte_carlo_summary, paper_snapshot):
    market = get_value(best, ["Market", "market"], "-")
    exit_model = get_value(best, ["Exit Model", "exit_model"], "-")
    stop_type = get_value(best, ["stop_type"], "-")
    atr = get_value(best, ["atr_multiple"], "-")
    hh = get_value(best, ["require_new_higher_high"], False)

    wf_light = light_from_text(walk_forward_report)
    mc_light = monte_carlo_summary.get("Traffic Light", "Saknas") if isinstance(monte_carlo_summary, dict) else "Saknas"
    robust = robustness_report.get("is_robust") if isinstance(robustness_report, dict) else False

    hh_text = "med HH-filter" if hh else "utan HH-filter"

    if conclusion == "ALGO_READY_CANDIDATE":
        headline = "Strategin ser stark ut, men den bör fortfarande verifieras praktiskt innan live."
    elif "GUL" in str(mc_light).upper():
        headline = "Strategin är lovande, men Monte Carlo är fortfarande gul. Paper trading är nästa rimliga steg."
    else:
        headline = "Strategin är intressant men behöver mer test innan live."

    paper_status = paper_snapshot.get("status", "Saknas") if isinstance(paper_snapshot, dict) else "Saknas"

    return (
        f"{headline}\n\n"
        f"Bästa kandidat just nu är {market} daily med {exit_model}, {stop_type} "
        f"{atr if stop_type == 'ATR' else ''} och {hh_text}. "
        f"Walk Forward är {wf_light.lower()}, Robustness är {'grön' if robust else 'inte godkänd'}, "
        f"och Monte Carlo är {mc_light}. Paper-status: {paper_status}."
    )


def show_metric_row(items):
    columns = st.columns(len(items))
    for col, (label, value) in zip(columns, items):
        col.metric(label, value)


def compact_table(records, columns, max_rows=10):
    df = as_df(records)
    if df.empty:
        st.info("Ingen data att visa.")
        return

    existing_columns = [c for c in columns if c in df.columns]
    if not existing_columns:
        st.dataframe(df.head(max_rows), use_container_width=True)
        return

    st.dataframe(df[existing_columns].head(max_rows), use_container_width=True)


# ==========================================================
# Page
# ==========================================================

st.title("EdgeCraft One-Click Optimizer")
st.caption("Välj strategi → välj marknadsuniversum → optimera → få en tydlig slutsats.")

with st.sidebar:
    st.header("Inställningar")

    strategy_names = get_strategy_names()
    strategy_name = st.selectbox("Strategi", strategy_names)

    universe_name = st.selectbox(
        "Marknadsuniversum",
        ["Core 5", "Nasdaq 100", "S&P 500", "Custom"],
        index=0,
    )

    custom_symbols = ""
    if universe_name == "Custom":
        custom_symbols = st.text_area(
            "Egna tickers",
            value="SPY, QQQ, AAPL, MSFT, NVDA",
            help="Skriv tickers separerade med komma eller ny rad.",
        )

    max_symbols = st.number_input(
        "Max antal symboler",
        min_value=0,
        value=0,
        step=10,
        help="0 betyder hela valt universum. Använd t.ex. 30 om du vill testa snabbare.",
    )

    start = st.text_input("Startdatum", "2015-01-01")

    initial_capital = st.number_input(
        "Startkapital",
        min_value=1000,
        value=100000,
        step=10000,
    )

    min_trades = st.number_input(
        "Minsta antal trades",
        min_value=1,
        value=30,
        step=1,
    )

    timeframes = DEFAULT_TIMEFRAMES

markets = get_market_universe(universe_name, custom_symbols, max_symbols)

with st.expander("Visa valt marknadsuniversum", expanded=False):
    st.write(f"Antal symboler: {len(markets)}")
    st.write(", ".join(markets))


if st.button("OPTIMERA", type="primary", use_container_width=True):
    with st.spinner(f"EdgeCraft testar {len(markets)} symboler..."):
        output = run_full_optimization_pipeline(
            strategy_name=strategy_name,
            start=start,
            initial_capital=initial_capital,
            min_trades=min_trades,
            markets=markets,
            timeframes=timeframes,
        )

    conclusion = get_value(
        output,
        ["conclusion", "status", "verdict", "final_decision", "decision"],
        "UNKNOWN",
    )

    raw_best = get_value(
        output,
        ["best_combination", "best_result", "best", "best_row"],
        {},
    )

    best = best_exit_candidate(output, raw_best)

    robustness_report = get_value(output, ["robustness_report"], {})
    walk_forward_report = get_value(output, ["walk_forward_report"], "")
    monte_carlo_summary = get_value(output, ["monte_carlo_summary"], {})
    paper_snapshot = get_value(output, ["paper_trading_snapshot"], {})

    st.markdown("## Executive Summary")

    status_color = "🟢" if conclusion == "ALGO_READY_CANDIDATE" else "🟡" if conclusion == "NEEDS_MORE_TESTING" else "🔴"

    st.markdown(
        f"""
        <div style="padding:22px;border-radius:16px;border:1px solid #2f3b52;background:#0f172a;color:white;">
            <h2 style="margin:0;">{status_color} {strategy_name}</h2>
            <p style="font-size:22px;margin:6px 0 0 0;"><b>Status:</b> {conclusion}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write("")

    show_metric_row([
        ("Marknad", get_value(best, ["Market", "market"], "-")),
        ("Exit", get_value(best, ["Exit Model", "exit_model"], "-")),
        ("Score", format_number(get_value(best, ["EdgeCraft Score", "score"], 0))),
        ("Profit Factor", format_number(get_value(best, ["Profit Factor", "profit_factor"], 0))),
    ])

    show_metric_row([
        ("Winrate", format_percent(get_value(best, ["Winrate", "winrate"], 0))),
        ("Trades", format_plain(get_value(best, ["Trades", "trades"], 0))),
        ("Max DD", format_percent(get_value(best, ["Max Drawdown", "max_drawdown"], 0))),
        ("Return", format_percent(get_value(best, ["Total Return", "return"], 0))),
    ])

    st.markdown("### Bästa parametrar")

    show_metric_row([
        ("Stop", format_plain(get_value(best, ["stop_type"], "-"))),
        ("ATR", format_plain(get_value(best, ["atr_multiple"], "-"))),
        ("Exit days", format_plain(get_value(best, ["exit_days"], "-"))),
        ("HH-filter", "JA" if get_value(best, ["require_new_higher_high"], False) else "NEJ"),
    ])

    st.markdown("### Trafikljus")

    screening_score = get_value(best, ["EdgeCraft Score", "score"], 0)

    show_metric_row([
        ("Screening", light_from_score(screening_score, green=70, yellow=50)),
        ("Robustness", light_from_bool(robustness_report.get("is_robust", False))),
        ("Walk Forward", light_from_text(walk_forward_report)),
        ("Monte Carlo", monte_carlo_summary.get("Traffic Light", "⚪ Saknas") if monte_carlo_summary else "⚪ Saknas"),
    ])

    st.markdown("### Enkel bedömning")
    st.info(
        build_human_assessment(
            conclusion=conclusion,
            best=best,
            robustness_report=robustness_report,
            walk_forward_report=walk_forward_report,
            monte_carlo_summary=monte_carlo_summary,
            paper_snapshot=paper_snapshot,
        )
    )

    st.markdown("### Paper Trading just nu")

    if paper_snapshot:
        levels = paper_snapshot.get("levels") or {}
        show_metric_row([
            ("Status", paper_snapshot.get("status", "-")),
            ("I position", "JA" if paper_snapshot.get("in_position") else "NEJ"),
            ("Senaste close", format_plain(paper_snapshot.get("latest_close", "-"))),
            ("Senaste datum", format_plain(paper_snapshot.get("latest_date", "-"))),
        ])

        show_metric_row([
            ("Entry", format_plain(levels.get("entry_price", "-"))),
            ("Stop", format_plain(levels.get("stop_price", "-"))),
            ("Target", format_plain(levels.get("target_price", "-"))),
        ])
    else:
        st.info("Ingen paper trading-data.")

    st.markdown("---")

    st.markdown("## Fördjupning")

    top_candidates = get_value(output, ["top_candidates"], [])
    exit_results = get_value(output, ["exit_results"], [])
    robustness_results = get_value(output, ["robustness_results"], [])
    walk_forward_results = get_value(output, ["walk_forward_results"], [])
    monte_carlo_results = get_value(output, ["monte_carlo_results"], [])
    all_results = get_value(output, ["results"], [])

    with st.expander("1. Toppkandidater", expanded=False):
        compact_table(
            top_candidates,
            [
                "Market", "Timeframe", "EdgeCraft Score", "Profit Factor", "Winrate",
                "Max Drawdown", "Trades", "Total Return", "stop_type", "atr_multiple",
                "exit_days", "require_new_higher_high",
            ],
            max_rows=10,
        )

    with st.expander("2. Exit Research", expanded=False):
        compact_table(
            exit_results,
            [
                "Market", "Timeframe", "Exit Model", "EdgeCraft Score", "Profit Factor",
                "Winrate", "Max Drawdown", "Trades", "Total Return", "stop_type",
                "atr_multiple", "exit_days", "require_new_higher_high",
            ],
            max_rows=15,
        )

    with st.expander("3. Robustness", expanded=False):
        if robustness_report:
            show_metric_row([
                ("Status", robustness_report.get("status", "-")),
                ("Robust?", "JA" if robustness_report.get("is_robust") else "NEJ"),
                ("Robusta rader", robustness_report.get("robust_rows", 0)),
                ("Robust ratio", format_percent(float(robustness_report.get("robust_ratio", 0)) * 100)),
            ])
            st.write(robustness_report.get("message", ""))

        compact_table(
            robustness_results,
            [
                "Market", "Timeframe", "EdgeCraft Score", "Profit Factor", "Winrate",
                "Max Drawdown", "Trades", "Total Return", "Exit Model",
            ],
            max_rows=10,
        )

    with st.expander("4. Walk Forward", expanded=False):
        st.text(walk_forward_report or "Ingen Walk Forward-data.")

        compact_table(
            walk_forward_results,
            ["Window", "Start Trade", "End Trade", "Trades", "Test PF", "Test Return", "Test Drawdown", "Pass"],
            max_rows=20,
        )

    with st.expander("5. Monte Carlo", expanded=False):
        if monte_carlo_summary:
            show_metric_row([
                ("MC Score", monte_carlo_summary.get("Monte Carlo Score", "-")),
                ("Trafikljus", monte_carlo_summary.get("Traffic Light", "-")),
                ("Vinstsannolikhet", format_percent(monte_carlo_summary.get("Profit Probability %", 0))),
                ("Sämsta DD", format_percent(monte_carlo_summary.get("Worst Max Drawdown %", 0))),
            ])

        compact_table(
            monte_carlo_results,
            ["Simulation", "Final Equity", "Total Return", "Max Drawdown", "Trades"],
            max_rows=20,
        )

    with st.expander("6. Alla screening-resultat", expanded=False):
        compact_table(
            all_results,
            [
                "Strategy", "Market", "Timeframe", "EdgeCraft Score", "Profit Factor",
                "Winrate", "Max Drawdown", "Trades", "Total Return", "stop_type",
                "atr_multiple", "exit_days", "require_new_higher_high", "Approved",
            ],
            max_rows=100,
        )

    with st.expander("Debug: komplett output", expanded=False):
        st.json(output)
