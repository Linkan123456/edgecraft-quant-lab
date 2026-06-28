"""
EdgeCraft Quant Lab
Trade Tracker Engine

Purpose:
- Track every trade
- Store trades safely
- Prepare data for AI pattern analysis
- Support strategy improvement based on real trades

Version: 1.0
"""

from pathlib import Path
from datetime import datetime
import pandas as pd


TRADE_LOG_PATH = Path("data/trade_log.csv")


REQUIRED_COLUMNS = [
    "trade_id",
    "created_at",
    "strategy",
    "market",
    "timeframe",
    "direction",
    "entry_date",
    "entry_price",
    "stop_price",
    "target_price",
    "exit_date",
    "exit_price",
    "result_r",
    "profit_loss",
    "status",
    "setup_quality",
    "notes",
]


def ensure_trade_log_exists():
    """
    Create trade log file if it does not exist.
    """

    TRADE_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    if not TRADE_LOG_PATH.exists():
        df = pd.DataFrame(columns=REQUIRED_COLUMNS)
        df.to_csv(TRADE_LOG_PATH, index=False)


def load_trades():
    """
    Load all tracked trades.
    """

    ensure_trade_log_exists()
    return pd.read_csv(TRADE_LOG_PATH)


def save_trades(df):
    """
    Save trade dataframe.
    """

    TRADE_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(TRADE_LOG_PATH, index=False)


def create_trade_id():
    """
    Create unique trade id.
    """

    return datetime.now().strftime("TRD-%Y%m%d-%H%M%S")


def log_trade(
    strategy,
    market,
    timeframe,
    direction,
    entry_date,
    entry_price,
    stop_price,
    target_price,
    exit_date="",
    exit_price="",
    result_r="",
    profit_loss="",
    status="OPEN",
    setup_quality="",
    notes="",
):
    """
    Log a new trade.
    """

    ensure_trade_log_exists()

    df = load_trades()

    trade = {
        "trade_id": create_trade_id(),
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "strategy": strategy,
        "market": market,
        "timeframe": timeframe,
        "direction": direction,
        "entry_date": entry_date,
        "entry_price": entry_price,
        "stop_price": stop_price,
        "target_price": target_price,
        "exit_date": exit_date,
        "exit_price": exit_price,
        "result_r": result_r,
        "profit_loss": profit_loss,
        "status": status,
        "setup_quality": setup_quality,
        "notes": notes,
    }

    df = pd.concat([df, pd.DataFrame([trade])], ignore_index=True)
    save_trades(df)

    return trade


def basic_trade_stats(df=None):
    """
    Calculate basic trade statistics.
    """

    if df is None:
        df = load_trades()

    if df.empty:
        return {
            "total_trades": 0,
            "closed_trades": 0,
            "winrate": 0,
            "average_r": 0,
            "total_r": 0,
        }

    closed = df[df["status"].astype(str).str.upper() == "CLOSED"].copy()

    if closed.empty:
        return {
            "total_trades": len(df),
            "closed_trades": 0,
            "winrate": 0,
            "average_r": 0,
            "total_r": 0,
        }

    closed["result_r"] = pd.to_numeric(closed["result_r"], errors="coerce").fillna(0)

    wins = closed[closed["result_r"] > 0]

    return {
        "total_trades": len(df),
        "closed_trades": len(closed),
        "winrate": round(len(wins) / len(closed) * 100, 2),
        "average_r": round(closed["result_r"].mean(), 3),
        "total_r": round(closed["result_r"].sum(), 3),
    }


def analyze_trade_patterns(df=None):
    """
    First simple AI-prep analysis.
    Later this will feed the AI improvement engine.
    """

    if df is None:
        df = load_trades()

    if df.empty:
        return {
            "status": "NO_TRADES",
            "insights": ["Inga trades finns ännu."],
        }

    insights = []
    stats = basic_trade_stats(df)

    insights.append(f"Totalt antal trades: {stats['total_trades']}")
    insights.append(f"Stängda trades: {stats['closed_trades']}")
    insights.append(f"Winrate: {stats['winrate']}%")
    insights.append(f"Average R: {stats['average_r']}")
    insights.append(f"Total R: {stats['total_r']}")

    if stats["closed_trades"] < 20:
        insights.append("För få stängda trades för säkra slutsatser. Samla minst 20–30 trades först.")

    if stats["average_r"] > 0:
        insights.append("Strategin visar positiv expectancy i nuvarande tradehistorik.")
    elif stats["closed_trades"] > 0:
        insights.append("Strategin visar ännu inte positiv expectancy. Vi bör analysera filter och setup-kvalitet.")

    return {
        "status": "OK",
        "stats": stats,
        "insights": insights,
    }