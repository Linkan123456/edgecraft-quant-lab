# engine/monte_carlo.py
# EdgeCraft Quant Lab v0.51

import pandas as pd
import numpy as np

from engine.scoring import calculate_monte_carlo_score, get_traffic_light


def run_monte_carlo_simulation(
    trades_df,
    initial_capital=100000,
    simulations=1000,
    random_seed=42
):
    if trades_df is None or trades_df.empty:
        return pd.DataFrame(), {}

    if "Return %" not in trades_df.columns:
        return pd.DataFrame(), {}

    np.random.seed(random_seed)

    trade_returns = trades_df["Return %"].dropna().values / 100

    if len(trade_returns) == 0:
        return pd.DataFrame(), {}

    simulation_results = []

    for sim in range(simulations):
        shuffled_returns = np.random.choice(
            trade_returns,
            size=len(trade_returns),
            replace=True
        )

        equity = initial_capital
        equity_curve = []

        for trade_return in shuffled_returns:
            equity = equity * (1 + trade_return)
            equity_curve.append(equity)

        equity_series = pd.Series(equity_curve)

        final_equity = equity_series.iloc[-1]
        total_return = (final_equity / initial_capital - 1) * 100

        running_max = equity_series.cummax()
        drawdown = (equity_series / running_max - 1) * 100
        max_drawdown = abs(drawdown.min())

        simulation_results.append({
            "Simulation": sim + 1,
            "Final Equity": round(final_equity, 2),
            "Total Return": round(total_return, 2),
            "Max Drawdown": round(max_drawdown, 2),
            "Trades": len(shuffled_returns)
        })

    monte_carlo_df = pd.DataFrame(simulation_results)

    summary = generate_monte_carlo_summary(
        monte_carlo_df=monte_carlo_df,
        initial_capital=initial_capital
    )

    return monte_carlo_df, summary


def generate_monte_carlo_summary(
    monte_carlo_df,
    initial_capital=100000
):
    if monte_carlo_df is None or monte_carlo_df.empty:
        return {}

    profitable_runs = monte_carlo_df[
        monte_carlo_df["Final Equity"] > initial_capital
    ]

    loss_runs = monte_carlo_df[
        monte_carlo_df["Final Equity"] <= initial_capital
    ]

    summary = {
        "Simulations": len(monte_carlo_df),
        "Profitable Runs": len(profitable_runs),
        "Losing Runs": len(loss_runs),
        "Profit Probability %": round(
            len(profitable_runs) / len(monte_carlo_df) * 100,
            2
        ),
        "Average Final Equity": round(
            monte_carlo_df["Final Equity"].mean(),
            2
        ),
        "Median Final Equity": round(
            monte_carlo_df["Final Equity"].median(),
            2
        ),
        "Worst Final Equity": round(
            monte_carlo_df["Final Equity"].min(),
            2
        ),
        "Best Final Equity": round(
            monte_carlo_df["Final Equity"].max(),
            2
        ),
        "Average Return %": round(
            monte_carlo_df["Total Return"].mean(),
            2
        ),
        "Median Return %": round(
            monte_carlo_df["Total Return"].median(),
            2
        ),
        "Worst Return %": round(
            monte_carlo_df["Total Return"].min(),
            2
        ),
        "Best Return %": round(
            monte_carlo_df["Total Return"].max(),
            2
        ),
        "Average Max Drawdown %": round(
            monte_carlo_df["Max Drawdown"].mean(),
            2
        ),
        "Median Max Drawdown %": round(
            monte_carlo_df["Max Drawdown"].median(),
            2
        ),
        "Worst Max Drawdown %": round(
            monte_carlo_df["Max Drawdown"].max(),
            2
        ),
        "Best Max Drawdown %": round(
            monte_carlo_df["Max Drawdown"].min(),
            2
        ),
    }

    monte_carlo_score = calculate_monte_carlo_score(summary)

    summary["Monte Carlo Score"] = monte_carlo_score
    summary["Traffic Light"] = get_traffic_light(monte_carlo_score)

    return summary


def generate_monte_carlo_report(summary):
    if summary is None or len(summary) == 0:
        return "Ingen Monte Carlo-data hittades."

    lines = []

    lines.append("=" * 60)
    lines.append("EDGECRAFT MONTE CARLO REPORT v0.51")
    lines.append("=" * 60)
    lines.append("")

    lines.append(f"Antal simuleringar: {summary['Simulations']}")
    lines.append(f"Sannolikhet för vinst: {summary['Profit Probability %']}%")
    lines.append("")
    lines.append(f"Monte Carlo Score: {summary['Monte Carlo Score']}")
    lines.append(f"Trafikljus: {summary['Traffic Light']}")
    lines.append("")
    lines.append(f"Genomsnittligt slutvärde: {summary['Average Final Equity']}")
    lines.append(f"Median slutvärde: {summary['Median Final Equity']}")
    lines.append(f"Sämsta slutvärde: {summary['Worst Final Equity']}")
    lines.append(f"Bästa slutvärde: {summary['Best Final Equity']}")
    lines.append("")
    lines.append(f"Genomsnittlig avkastning: {summary['Average Return %']}%")
    lines.append(f"Medianavkastning: {summary['Median Return %']}%")
    lines.append(f"Sämsta avkastning: {summary['Worst Return %']}%")
    lines.append(f"Bästa avkastning: {summary['Best Return %']}%")
    lines.append("")
    lines.append(f"Genomsnittlig Max Drawdown: {summary['Average Max Drawdown %']}%")
    lines.append(f"Median Max Drawdown: {summary['Median Max Drawdown %']}%")
    lines.append(f"Sämsta Max Drawdown: {summary['Worst Max Drawdown %']}%")
    lines.append("")

    lines.append("BEDÖMNING")
    lines.append("----------------------------")

    monte_carlo_score = summary["Monte Carlo Score"]

    if monte_carlo_score >= 70:
        lines.append("Strategin klarar Monte Carlo-testet starkt.")
        lines.append("Resultatet verkar tåla slumpmässig omkastning av trades.")
    elif monte_carlo_score >= 50:
        lines.append("Strategin klarar Monte Carlo-testet delvis.")
        lines.append("Strategin är intressant men risken behöver granskas vidare.")
    else:
        lines.append("Strategin klarar inte Monte Carlo-testet tillräckligt bra.")
        lines.append("Resultatet är känsligt för trade-ordning och slump.")

    lines.append("")
    lines.append("Nästa steg: förbättra Monte Carlo-sidan med score och trafikljus.")
    lines.append("=" * 60)

    return "\n".join(lines)