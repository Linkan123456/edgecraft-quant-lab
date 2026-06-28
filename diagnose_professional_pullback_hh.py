# diagnose_professional_pullback_hh.py
# EdgeCraft Quant Lab diagnostic
# Purpose: Compare Professional Pullback with HH-filter OFF vs ON.

import pandas as pd

from data.downloader import load_market_data
from engine.core_backtest import run_strategy_backtest
from engine.scoring import calculate_edgecraft_score
from strategies.registry import get_strategy_config


STRATEGY_NAME = "Professional Pullback"
TICKER = "AMD"
TIMEFRAME = "1d"
START = "2015-01-01"
END = None
INITIAL_CAPITAL = 100000
MIN_TRADES = 30

BASE_PARAMETERS = {
    "ma_fast": 20,
    "ma_slow": 50,
    "ma_long": 200,
    "pullback_min_days": 2,
    "pullback_max_days": 10,
    "near_high_pct": 10,
    "volume_filter": "None",
    "entry_trigger": "BreakPreviousHigh",
    "stop_type": "ATR",
    "atr_period": 14,
    "atr_multiple": 1.0,
    "exit_days": 10,
    "risk_reward": 3,
}


def safe_get(stats, key, default=0):
    try:
        return stats.get(key, default)
    except Exception:
        return default


def run_case(data: pd.DataFrame, require_hh: bool):
    parameters = BASE_PARAMETERS.copy()
    parameters["require_new_higher_high"] = require_hh

    config = get_strategy_config(STRATEGY_NAME)
    signal_data = config["signal_function"](
        data=data.copy(),
        **{**config["default_parameters"], **parameters},
    )

    buy_signals = int(signal_data.get("BuySignal", pd.Series(dtype=bool)).fillna(False).sum())
    new_higher_high_signals = int(signal_data.get("NewHigherHigh", pd.Series(dtype=bool)).fillna(False).sum()) if "NewHigherHigh" in signal_data.columns else 0

    result = run_strategy_backtest(
        data=data.copy(),
        strategy_name=STRATEGY_NAME,
        initial_capital=INITIAL_CAPITAL,
        parameters=parameters,
        market=TICKER,
        timeframe=TIMEFRAME,
    )

    stats = result.stats or {}
    score = calculate_edgecraft_score(stats=stats, min_trades=MIN_TRADES)

    return {
        "HH-filter": require_hh,
        "BuySignals": buy_signals,
        "NewHigherHighSignals": new_higher_high_signals,
        "Trades": safe_get(stats, "Trades", 0),
        "Profit Factor": round(float(safe_get(stats, "Profit Factor", 0)), 3),
        "Winrate": round(float(safe_get(stats, "Winrate", 0)), 2),
        "Max Drawdown": round(float(safe_get(stats, "Max Drawdown", 0)), 2),
        "Total Return": round(float(safe_get(stats, "Total Return", 0)), 2),
        "EdgeCraft Score": round(float(score), 2),
    }


def main():
    print("=" * 70)
    print("EDGECRAFT DIAGNOSTIC: Professional Pullback HH-filter")
    print("=" * 70)
    print(f"Strategy: {STRATEGY_NAME}")
    print(f"Ticker:   {TICKER}")
    print(f"Period:   {START} -> latest")
    print(f"Params:   {BASE_PARAMETERS}")
    print("=" * 70)

    data = load_market_data(
        ticker=TICKER,
        start=START,
        end=END,
        interval=TIMEFRAME,
    )

    if data is None or data.empty:
        raise RuntimeError("No market data loaded. Check downloader/data source.")

    rows = [
        run_case(data, require_hh=False),
        run_case(data, require_hh=True),
    ]

    df = pd.DataFrame(rows)
    print(df.to_string(index=False))
    print("=" * 70)

    false_row = rows[0]
    true_row = rows[1]

    if true_row["BuySignals"] == 0 or true_row["Trades"] == 0:
        print("DIAGNOS: HH=True är mycket strikt och producerar inga/för få affärer för denna setup.")
    elif true_row["EdgeCraft Score"] < false_row["EdgeCraft Score"]:
        print("DIAGNOS: HH=True fungerar, men får lägre score än HH=False för denna setup.")
    elif true_row["EdgeCraft Score"] > false_row["EdgeCraft Score"]:
        print("DIAGNOS: HH=True fungerar och ser bättre ut än HH=False för denna setup.")
    else:
        print("DIAGNOS: HH=True och HH=False ger mycket liknande resultat. Kontrollera signalregeln vidare.")


if __name__ == "__main__":
    main()
