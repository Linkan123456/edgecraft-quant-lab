# engine/backtester.py
# EdgeCraft Quant Lab
#
# Backtester v1.1
# Uses strategy-generated StopPrice when available.
# This makes stop_type / ATR / UnderEntryCandle / UnderPreviousCandle affect results.

import pandas as pd


def _safe_float(value, default=None):
    try:
        if pd.isna(value):
            return default
        return float(value)
    except Exception:
        return default


def run_backtest(
    data: pd.DataFrame,
    initial_capital: float,
    parameters=None,
):
    if parameters is None:
        parameters = {}

    df = data.copy()

    risk_reward = parameters.get("risk_reward", None)
    stop_loss_pct = parameters.get("stop_loss_pct", 5)

    cash = initial_capital
    position = 0
    entry_price = 0
    entry_date = None
    stop_price = None
    target_price = None

    equity_curve = []
    trades = []

    for i in range(len(df)):
        row = df.iloc[i]
        date = df.index[i]
        close = _safe_float(row.get("Close", 0), 0)

        equity_curve.append(cash + position * close)

        if position == 0 and row.get("BuySignal", False):
            position = cash / close
            entry_price = close
            entry_date = date
            cash = 0

            strategy_stop = _safe_float(row.get("StopPrice", None), None)

            if strategy_stop is not None and strategy_stop > 0 and strategy_stop < entry_price:
                stop_price = strategy_stop
                stop_source = "Strategy StopPrice"
            else:
                stop_price = entry_price * (1 - stop_loss_pct / 100)
                stop_source = f"Fallback {stop_loss_pct}% Stop"

            if risk_reward is not None:
                risk_per_share = entry_price - stop_price

                if risk_per_share > 0:
                    target_price = entry_price + (risk_per_share * float(risk_reward))
                else:
                    target_price = None
            else:
                target_price = None

        elif position > 0:
            exit_reason = None
            exit_price = close

            if stop_price is not None and close <= stop_price:
                exit_reason = "Stop Loss"
                exit_price = close

            elif target_price is not None and close >= target_price:
                exit_reason = f"{risk_reward}R Target"
                exit_price = close

            elif row.get("SellSignal", False):
                exit_reason = "Sell Signal"
                exit_price = close

            if exit_reason:
                cash = position * exit_price
                pnl = cash - position * entry_price
                ret_pct = (exit_price / entry_price - 1) * 100

                trades.append({
                    "Entry Date": entry_date,
                    "Exit Date": date,
                    "Entry": round(entry_price, 2),
                    "Exit": round(exit_price, 2),
                    "Stop": round(stop_price, 2) if stop_price is not None else None,
                    "Target": round(target_price, 2) if target_price is not None else None,
                    "Return %": round(ret_pct, 2),
                    "PnL": round(pnl, 2),
                    "Exit Reason": exit_reason,
                    "Stop Source": stop_source,
                })

                position = 0
                entry_price = 0
                entry_date = None
                stop_price = None
                target_price = None

    if position > 0:
        final_close = _safe_float(df.iloc[-1].get("Close", 0), 0)
        final_date = df.index[-1]

        cash = position * final_close
        pnl = cash - position * entry_price
        ret_pct = (final_close / entry_price - 1) * 100

        trades.append({
            "Entry Date": entry_date,
            "Exit Date": final_date,
            "Entry": round(entry_price, 2),
            "Exit": round(final_close, 2),
            "Stop": round(stop_price, 2) if stop_price is not None else None,
            "Target": round(target_price, 2) if target_price is not None else None,
            "Return %": round(ret_pct, 2),
            "PnL": round(pnl, 2),
            "Exit Reason": "End of Data",
            "Stop Source": stop_source if "stop_source" in locals() else None,
        })

        position = 0

    df["Equity"] = equity_curve
    trades_df = pd.DataFrame(trades)

    return df, trades_df
