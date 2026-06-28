# engine/paper_trading.py
# EdgeCraft Quant Lab
#
# Paper Trading v1
# No broker orders. No real trading.
# This file must NOT import optimization_pipeline.py.

from datetime import datetime

from data.downloader import load_market_data
from engine.strategy_runner import StrategyRunner


def _safe_float(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return default


def _extract_risk_reward(candidate=None, default=2):
    if candidate is None:
        return default

    exit_model = candidate.get("Exit Model") or candidate.get("exit_model")

    if not exit_model:
        return default

    try:
        return int(str(exit_model).replace("R", "").strip())
    except Exception:
        return default


def build_trade_levels(
    entry_price,
    risk_reward=2,
    stop_loss_pct=5,
):
    entry_price = _safe_float(entry_price)
    risk_reward = _safe_float(risk_reward, 2)
    stop_loss_pct = _safe_float(stop_loss_pct, 5)

    stop_price = entry_price * (1 - stop_loss_pct / 100)
    risk_per_share = entry_price - stop_price
    target_price = entry_price + (risk_per_share * risk_reward)

    return {
        "entry_price": round(entry_price, 2),
        "stop_price": round(stop_price, 2),
        "target_price": round(target_price, 2),
        "risk_reward": risk_reward,
        "stop_loss_pct": stop_loss_pct,
    }


def get_latest_signal_snapshot(
    strategy_name,
    market,
    timeframe="1d",
    start="2015-01-01",
    end=None,
    initial_capital=100000,
    parameters=None,
):
    if parameters is None:
        parameters = {}

    if end is None:
        end = datetime.today().strftime("%Y-%m-%d")

    data = load_market_data(
        ticker=market,
        start=start,
        end=end,
        interval=timeframe,
    )

    if data is None or data.empty:
        return {
            "status": "NO_DATA",
            "message": f"Ingen data hittades för {market} {timeframe}.",
            "market": market,
            "timeframe": timeframe,
        }

    runner = StrategyRunner(strategy_name)

    signal_data = runner.apply_signals(
        data=data.copy(),
        **parameters,
    )

    if signal_data is None or signal_data.empty:
        return {
            "status": "NO_SIGNAL_DATA",
            "message": "Strategin gav ingen signaldata.",
            "market": market,
            "timeframe": timeframe,
        }

    latest_row = signal_data.iloc[-1]
    latest_date = signal_data.index[-1]
    latest_close = _safe_float(latest_row.get("Close", 0))

    latest_buy_signal = bool(latest_row.get("BuySignal", False))
    latest_sell_signal = bool(latest_row.get("SellSignal", False))

    buy_signal_mask = signal_data.get("BuySignal", False)
    sell_signal_mask = signal_data.get("SellSignal", False)

    buy_signals = signal_data[buy_signal_mask == True] if hasattr(buy_signal_mask, "__len__") else signal_data.iloc[0:0]
    sell_signals = signal_data[sell_signal_mask == True] if hasattr(sell_signal_mask, "__len__") else signal_data.iloc[0:0]

    latest_buy_date = None
    latest_buy_price = None

    if buy_signals is not None and not buy_signals.empty:
        latest_buy_date = buy_signals.index[-1]
        latest_buy_price = _safe_float(buy_signals.iloc[-1].get("Close", 0))

    latest_sell_date = None

    if sell_signals is not None and not sell_signals.empty:
        latest_sell_date = sell_signals.index[-1]

    in_position = False

    if latest_buy_date is not None:
        if latest_sell_date is None or latest_buy_date > latest_sell_date:
            in_position = True

    risk_reward = parameters.get("risk_reward", 2)
    stop_loss_pct = parameters.get("stop_loss_pct", 5)

    levels = None
    if latest_buy_price:
        levels = build_trade_levels(
            entry_price=latest_buy_price,
            risk_reward=risk_reward,
            stop_loss_pct=stop_loss_pct,
        )

    if latest_buy_signal:
        status = "BUY_SIGNAL_TODAY"
        message = "Ny köpsignal på senaste candle."
    elif in_position:
        status = "IN_POSITION"
        message = "Strategin är redan i en öppen paper-position enligt senaste signalflödet."
    elif latest_sell_signal:
        status = "SELL_SIGNAL_TODAY"
        message = "Säljsignal på senaste candle."
    else:
        status = "NO_ACTIVE_SIGNAL"
        message = "Ingen aktiv köpsignal just nu."

    return {
        "status": status,
        "message": message,
        "strategy": strategy_name,
        "market": market,
        "timeframe": timeframe,
        "latest_date": str(latest_date),
        "latest_close": round(latest_close, 2),
        "latest_buy_signal": latest_buy_signal,
        "latest_sell_signal": latest_sell_signal,
        "in_position": in_position,
        "latest_buy_date": str(latest_buy_date) if latest_buy_date is not None else None,
        "latest_buy_price": round(latest_buy_price, 2) if latest_buy_price else None,
        "latest_sell_date": str(latest_sell_date) if latest_sell_date is not None else None,
        "levels": levels,
    }


def run_paper_trading_check(
    strategy_name,
    candidate,
    start="2015-01-01",
    end=None,
    initial_capital=100000,
):
    if candidate is None:
        return {
            "status": "NO_CANDIDATE",
            "message": "Ingen kandidat skickades till Paper Trading.",
        }

    market = candidate.get("Market") or candidate.get("market")
    timeframe = candidate.get("Timeframe") or candidate.get("timeframe")

    if not market or not timeframe:
        return {
            "status": "INVALID_CANDIDATE",
            "message": "Kandidaten saknar Market eller Timeframe.",
            "candidate": candidate,
        }

    risk_reward = _extract_risk_reward(candidate, default=2)

    parameters = {
        "risk_reward": risk_reward,
        "stop_loss_pct": candidate.get("stop_loss_pct", 5),
    }

    snapshot = get_latest_signal_snapshot(
        strategy_name=strategy_name,
        market=market,
        timeframe=timeframe,
        start=start,
        end=end,
        initial_capital=initial_capital,
        parameters=parameters,
    )

    snapshot["paper_mode"] = True
    snapshot["real_orders"] = False
    snapshot["warning"] = "Paper Trading v1 är endast för simulering. Inga riktiga order skickas."

    return snapshot


def generate_paper_trading_report(snapshot):
    if snapshot is None:
        return "Ingen Paper Trading-data."

    lines = []
    lines.append("=" * 60)
    lines.append("EDGECRAFT PAPER TRADING v1")
    lines.append("=" * 60)
    lines.append("")
    lines.append(f"Status: {snapshot.get('status', 'N/A')}")
    lines.append(f"Bedömning: {snapshot.get('message', '')}")
    lines.append("")
    lines.append(f"Strategi: {snapshot.get('strategy', 'N/A')}")
    lines.append(f"Marknad: {snapshot.get('market', 'N/A')}")
    lines.append(f"Timeframe: {snapshot.get('timeframe', 'N/A')}")
    lines.append(f"Senaste datum: {snapshot.get('latest_date', 'N/A')}")
    lines.append(f"Senaste close: {snapshot.get('latest_close', 'N/A')}")
    lines.append("")
    lines.append(f"I position: {'JA' if snapshot.get('in_position') else 'NEJ'}")
    lines.append(f"Senaste köpsignal: {snapshot.get('latest_buy_date', 'N/A')}")
    lines.append(f"Senaste köpkurs: {snapshot.get('latest_buy_price', 'N/A')}")
    lines.append(f"Senaste säljsignal: {snapshot.get('latest_sell_date', 'N/A')}")
    lines.append("")

    levels = snapshot.get("levels")

    if levels:
        lines.append("TRADE LEVELS")
        lines.append("----------------------------")
        lines.append(f"Entry: {levels.get('entry_price')}")
        lines.append(f"Stop: {levels.get('stop_price')}")
        lines.append(f"Target: {levels.get('target_price')}")
        lines.append(f"Risk/Reward: {levels.get('risk_reward')}R")
        lines.append(f"Stop loss: {levels.get('stop_loss_pct')}%")
        lines.append("")

    lines.append("VIKTIGT")
    lines.append("----------------------------")
    lines.append("Detta är paper trading. Inga riktiga order skickas.")
    lines.append("Nästa steg är att logga paper trades över tid och jämföra mot backtest.")
    lines.append("=" * 60)

    return "\n".join(lines)
