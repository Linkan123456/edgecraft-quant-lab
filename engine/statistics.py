def calculate_statistics(df, trades_df, initial_capital):
    if df.empty or "Equity" not in df.columns:
        return {}

    final_equity = df["Equity"].iloc[-1]
    total_return = (final_equity / initial_capital - 1) * 100

    running_max = df["Equity"].cummax()
    drawdown = (df["Equity"] / running_max - 1) * 100
    max_drawdown = abs(drawdown.min())

    if trades_df.empty:
        return {
            "Total Return": round(total_return, 2),
            "Winrate": 0,
            "Profit Factor": 0,
            "Max Drawdown": round(max_drawdown, 2),
            "Trades": 0,
            "Avg Trade": 0,
        }

    wins = trades_df[trades_df["PnL"] > 0]
    losses = trades_df[trades_df["PnL"] < 0]

    winrate = len(wins) / len(trades_df) * 100
    gross_profit = wins["PnL"].sum()
    gross_loss = abs(losses["PnL"].sum())

    profit_factor = gross_profit / gross_loss if gross_loss > 0 else 999
    avg_trade = trades_df["Return %"].mean()

    return {
        "Total Return": round(total_return, 2),
        "Winrate": round(winrate, 2),
        "Profit Factor": round(profit_factor, 3),
        "Max Drawdown": round(max_drawdown, 2),
        "Trades": len(trades_df),
        "Avg Trade": round(avg_trade, 2),
    }