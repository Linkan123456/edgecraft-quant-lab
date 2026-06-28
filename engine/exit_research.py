# engine/exit_research.py
# EdgeCraft Quant Lab

import pandas as pd

from engine.market_timeframe_optimizer import run_market_timeframe_optimizer


EXIT_R_MULTIPLES = [2, 3, 4]


def _candidate_parameter_grid(candidate, r_multiple):
    """
    Build a one-combination parameter grid from the winning screening candidate,
    then add the exit model being tested.

    This prevents Exit Research from dropping the optimized strategy parameters.
    """

    parameter_keys = [
        "ma_fast",
        "ma_slow",
        "ma_long",
        "pullback_min_days",
        "pullback_max_days",
        "near_high_pct",
        "volume_filter",
        "entry_trigger",
        "stop_type",
        "atr_period",
        "atr_multiple",
        "exit_days",
        "require_new_higher_high",
    ]

    grid = {}

    for key in parameter_keys:
        if key in candidate:
            grid[key] = [candidate.get(key)]

    grid["risk_reward"] = [r_multiple]

    return grid


def _dedupe_candidates(top_candidates):
    """
    Remove duplicate candidates before Exit Research.
    Keeps the first occurrence of each unique market/timeframe/parameter set.
    """

    seen = set()
    unique = []

    for candidate in top_candidates:
        market = candidate.get("Market") or candidate.get("market")
        timeframe = candidate.get("Timeframe") or candidate.get("timeframe")

        key = (
            market,
            timeframe,
            candidate.get("ma_fast"),
            candidate.get("ma_slow"),
            candidate.get("ma_long"),
            candidate.get("pullback_min_days"),
            candidate.get("pullback_max_days"),
            candidate.get("near_high_pct"),
            candidate.get("volume_filter"),
            candidate.get("entry_trigger"),
            candidate.get("stop_type"),
            candidate.get("atr_period"),
            candidate.get("atr_multiple"),
            candidate.get("exit_days"),
            candidate.get("require_new_higher_high"),
        )

        if key in seen:
            continue

        seen.add(key)
        unique.append(candidate)

    return unique


def run_exit_research(
    strategy_name,
    top_candidates,
    start="2015-01-01",
    end=None,
    initial_capital=100000,
    min_trades=30,
):
    if not top_candidates:
        return pd.DataFrame(), "Inga toppkandidater skickades till Exit Research."

    rows = []
    unique_candidates = _dedupe_candidates(top_candidates)

    for candidate in unique_candidates:
        market = candidate.get("Market") or candidate.get("market")
        timeframe = candidate.get("Timeframe") or candidate.get("timeframe")

        if not market or not timeframe:
            continue

        for r_multiple in EXIT_R_MULTIPLES:
            parameter_grid = _candidate_parameter_grid(
                candidate=candidate,
                r_multiple=r_multiple,
            )

            try:
                results_df, _ = run_market_timeframe_optimizer(
                    strategy_name=strategy_name,
                    parameter_grid=parameter_grid,
                    start=start,
                    end=end,
                    initial_capital=initial_capital,
                    min_trades=min_trades,
                    markets=[market],
                    timeframes=[timeframe],
                )

                if results_df is None or results_df.empty:
                    continue

                if "risk_reward" in results_df.columns:
                    matches = results_df[results_df["risk_reward"] == r_multiple]
                    if not matches.empty:
                        row = matches.iloc[0].to_dict()
                    else:
                        row = results_df.iloc[0].to_dict()
                else:
                    row = results_df.iloc[0].to_dict()

                row["Exit Model"] = f"{r_multiple}R"
                row["R Multiple"] = r_multiple
                rows.append(row)

            except Exception as error:
                error_row = {
                    "Strategy": strategy_name,
                    "Market": market,
                    "Timeframe": timeframe,
                    "Exit Model": f"{r_multiple}R",
                    "R Multiple": r_multiple,
                    "Profit Factor": 0,
                    "Winrate": 0,
                    "Max Drawdown": 0,
                    "Trades": 0,
                    "Total Return": 0,
                    "EdgeCraft Score": 0,
                    "Approved": False,
                    "Error": str(error),
                }

                for key, values in parameter_grid.items():
                    if isinstance(values, list) and values:
                        error_row[key] = values[0]

                rows.append(error_row)

    exit_df = pd.DataFrame(rows)

    if exit_df.empty:
        return exit_df, "Exit Research gav inga resultat."

    exit_df = exit_df.sort_values(
        by=["EdgeCraft Score", "Profit Factor", "Total Return"],
        ascending=False,
    ).reset_index(drop=True)

    summary = generate_exit_research_summary(exit_df)

    return exit_df, summary


def generate_exit_research_summary(exit_df):
    if exit_df is None or exit_df.empty:
        return "Ingen exit-data hittades."

    best = exit_df.iloc[0]

    lines = []
    lines.append("=" * 60)
    lines.append("EDGECRAFT EXIT RESEARCH v0.10")
    lines.append("=" * 60)
    lines.append("")
    lines.append(f"Totalt antal exit-tester: {len(exit_df)}")
    lines.append("")
    lines.append("BÄSTA EXIT")
    lines.append("----------------------------")
    lines.append(f"Marknad: {best.get('Market', 'N/A')}")
    lines.append(f"Timeframe: {best.get('Timeframe', 'N/A')}")
    lines.append(f"Exit: {best.get('Exit Model', 'N/A')}")
    lines.append(f"Score: {best.get('EdgeCraft Score', 'N/A')}")
    lines.append(f"Profit Factor: {best.get('Profit Factor', 'N/A')}")
    lines.append(f"Winrate: {best.get('Winrate', 'N/A')}%")
    lines.append(f"Trades: {best.get('Trades', 'N/A')}")
    lines.append(f"Total Return: {best.get('Total Return', 'N/A')}%")
    lines.append("")
    lines.append("TOPPRESULTAT")
    lines.append("----------------------------")

    for _, row in exit_df.head(10).iterrows():
        lines.append(
            f"{row.get('Market', 'N/A')} | "
            f"{row.get('Timeframe', 'N/A')} | "
            f"{row.get('Exit Model', 'N/A')} | "
            f"Score {row.get('EdgeCraft Score', 'N/A')} | "
            f"PF {row.get('Profit Factor', 'N/A')} | "
            f"Trades {row.get('Trades', 'N/A')}"
        )

    lines.append("")
    lines.append("Nästa steg: Kör robusthetstest på bästa exit-kandidaterna.")
    lines.append("=" * 60)

    return "\n".join(lines)