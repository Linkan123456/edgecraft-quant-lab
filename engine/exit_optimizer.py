# engine/exit_optimizer.py
# EdgeCraft Quant Lab v0.72

import pandas as pd

from engine.core_backtest import run_strategy_backtest
from engine.scoring import calculate_edgecraft_score


DEFAULT_EXIT_VALUES = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 15, 20]


def detect_exit_parameter(parameter_grid):
    possible_names = [
        "exit_days",
        "exit_lookback",
        "exit_bars",
        "holding_period",
        "max_hold_days"
    ]

    for name in possible_names:
        if name in parameter_grid:
            return name

    return None


def run_exit_optimizer(
    data,
    strategy_name,
    base_parameters,
    parameter_grid,
    initial_capital=100000,
    min_trades=30,
    market="",
    timeframe="",
    exit_values=None
):
    if exit_values is None:
        exit_values = DEFAULT_EXIT_VALUES

    if data is None or data.empty:
        return pd.DataFrame(), "Ingen data hittades."

    exit_parameter = detect_exit_parameter(parameter_grid)

    if exit_parameter is None:
        return pd.DataFrame(), "Ingen exit-parameter hittades för strategin."

    results = []

    for exit_value in exit_values:
        parameters = base_parameters.copy()
        parameters[exit_parameter] = exit_value

        result = run_strategy_backtest(
            data=data,
            strategy_name=strategy_name,
            initial_capital=initial_capital,
            parameters=parameters,
            market=market,
            timeframe=timeframe
        )

        stats = result.stats

        score = calculate_edgecraft_score(
            stats=stats,
            min_trades=min_trades
        )

        row = {
            "Strategy": strategy_name,
            "Market": market,
            "Timeframe": timeframe,
            "Exit Parameter": exit_parameter,
            "Exit Value": exit_value,
            "Profit Factor": stats.get("Profit Factor", 0),
            "Winrate": stats.get("Winrate", 0),
            "Max Drawdown": stats.get("Max Drawdown", 0),
            "Trades": stats.get("Trades", 0),
            "Total Return": stats.get("Total Return", 0),
            "Avg Trade": stats.get("Avg Trade", 0),
            "EdgeCraft Score": score,
            "Approved": stats.get("Trades", 0) >= min_trades
        }

        row.update(parameters)

        results.append(row)

    results_df = pd.DataFrame(results)

    if results_df.empty:
        return results_df, "Inga exit-resultat skapades."

    results_df = results_df.sort_values(
        by=["EdgeCraft Score", "Profit Factor", "Total Return"],
        ascending=False
    )

    report = generate_exit_optimizer_report(
        results_df=results_df,
        exit_parameter=exit_parameter
    )

    return results_df, report


def generate_exit_optimizer_report(results_df, exit_parameter):
    if results_df is None or results_df.empty:
        return "Ingen exit-data hittades."

    approved_df = results_df[results_df["Approved"] == True].copy()

    lines = []

    lines.append("=" * 60)
    lines.append("EDGECRAFT EXIT OPTIMIZER REPORT v0.72")
    lines.append("=" * 60)
    lines.append("")
    lines.append(f"Exit-parameter: {exit_parameter}")
    lines.append(f"Totalt antal exit-tester: {len(results_df)}")
    lines.append(f"Godkända exit-tester: {len(approved_df)}")
    lines.append("")

    if approved_df.empty:
        lines.append("Ingen exit klarade minsta antal trades.")
        lines.append("=" * 60)
        return "\n".join(lines)

    best = approved_df.iloc[0]

    lines.append("BÄSTA EXIT")
    lines.append("----------------------------")
    lines.append(f"Exit Value: {best['Exit Value']}")
    lines.append(f"EdgeCraft Score: {best['EdgeCraft Score']}")
    lines.append(f"Profit Factor: {best['Profit Factor']}")
    lines.append(f"Winrate: {best['Winrate']}%")
    lines.append(f"Max Drawdown: {best['Max Drawdown']}%")
    lines.append(f"Trades: {int(best['Trades'])}")
    lines.append(f"Total Return: {best['Total Return']}%")
    lines.append("")

    lines.append("TOPP EXIT-VÄRDEN")
    lines.append("----------------------------")

    for _, row in approved_df.head(10).iterrows():
        lines.append(
            f"Exit {row['Exit Value']} | "
            f"Score {row['EdgeCraft Score']} | "
            f"PF {row['Profit Factor']} | "
            f"Trades {int(row['Trades'])}"
        )

    lines.append("")
    lines.append("BEDÖMNING")
    lines.append("----------------------------")

    top_scores = approved_df.head(5)["EdgeCraft Score"].tolist()

    if len(top_scores) >= 3:
        spread = max(top_scores) - min(top_scores)

        if spread <= 10:
            lines.append("Exit-resultaten visar en relativt stabil platå.")
            lines.append("Det minskar risken för överoptimering.")
        else:
            lines.append("Exit-resultaten är mer känsliga.")
            lines.append("Bästa exit bör verifieras med Walk Forward och Monte Carlo.")
    else:
        lines.append("För få godkända exit-värden för stark robusthetsbedömning.")

    lines.append("")
    lines.append("Nästa steg: koppla Exit Optimizer till Optimization Pipeline.")
    lines.append("=" * 60)

    return "\n".join(lines)