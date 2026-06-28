# engine/market_timeframe_optimizer.py
# EdgeCraft Quant Lab

import itertools
import pandas as pd

from data.downloader import load_market_data
from engine.core_backtest import run_strategy_backtest
from engine.scoring import calculate_edgecraft_score


DEFAULT_MARKETS = [
    "SPY", "QQQ", "AAPL", "MSFT", "NVDA",
]

DEFAULT_TIMEFRAMES = [
    "1d",
]


def build_parameter_combinations(parameter_grid=None):
    if not parameter_grid:
        return [{}]

    keys = list(parameter_grid.keys())
    values = list(parameter_grid.values())

    if not keys:
        return [{}]

    combinations = []

    for combination in itertools.product(*values):
        params = dict(zip(keys, combination))

        # Ignore duplicate ATR combinations when ATR isn't used.
        if (
            params.get("stop_type") != "ATR"
            and "atr_multiple" in params
        ):
            default_atr = parameter_grid.get("atr_multiple", [params["atr_multiple"]])[0]
            if params["atr_multiple"] != default_atr:
                continue

        combinations.append(params)

    return combinations


def _error_row(strategy_name, market, timeframe, error_message):
    return {
        "Strategy": strategy_name,
        "Market": market,
        "Timeframe": timeframe,
        "Profit Factor": 0,
        "Winrate": 0,
        "Max Drawdown": 0,
        "Trades": 0,
        "Total Return": 0,
        "Avg Trade": 0,
        "EdgeCraft Score": 0,
        "Approved": False,
        "Error": error_message,
    }


def run_market_timeframe_optimizer(
    strategy_name,
    parameter_grid=None,
    start="2015-01-01",
    end=None,
    initial_capital=100000,
    min_trades=30,
    markets=None,
    timeframes=None,
):
    if markets is None:
        markets = DEFAULT_MARKETS

    if timeframes is None:
        timeframes = DEFAULT_TIMEFRAMES

    parameter_sets = build_parameter_combinations(parameter_grid)
    results = []

    for market in markets:
        for timeframe in timeframes:
            try:
                data = load_market_data(
                    ticker=market,
                    start=start,
                    end=end,
                    interval=timeframe,
                )

                if data is None:
                    results.append(_error_row(strategy_name, market, timeframe, "Data is None"))
                    continue

                if data.empty:
                    results.append(_error_row(strategy_name, market, timeframe, "DataFrame is empty"))
                    continue

                for parameters in parameter_sets:
                    try:
                        result = run_strategy_backtest(
                            data=data,
                            strategy_name=strategy_name,
                            initial_capital=initial_capital,
                            parameters=parameters,
                            market=market,
                            timeframe=timeframe,
                        )

                        if result is None:
                            results.append(_error_row(strategy_name, market, timeframe, "Backtest returned None"))
                            continue

                        stats = getattr(result, "stats", None)

                        if not stats:
                            results.append(_error_row(strategy_name, market, timeframe, "Missing stats"))
                            continue

                        trades = stats.get("Trades", 0)

                        score = calculate_edgecraft_score(
                            stats=stats,
                            min_trades=min_trades,
                        )

                        row = {
                            "Strategy": strategy_name,
                            "Market": market,
                            "Timeframe": timeframe,
                            "Profit Factor": stats.get("Profit Factor", 0),
                            "Winrate": stats.get("Winrate", 0),
                            "Max Drawdown": stats.get("Max Drawdown", 0),
                            "Trades": trades,
                            "Total Return": stats.get("Total Return", 0),
                            "Avg Trade": stats.get("Avg Trade", 0),
                            "EdgeCraft Score": score,
                            "Approved": trades >= min_trades,
                            "Error": "",
                        }

                        row.update(parameters)
                        results.append(row)

                    except Exception as backtest_error:
                        results.append(
                            _error_row(
                                strategy_name,
                                market,
                                timeframe,
                                f"Backtest error: {backtest_error}",
                            )
                        )

            except Exception as data_error:
                results.append(
                    _error_row(
                        strategy_name,
                        market,
                        timeframe,
                        f"Data loading error: {data_error}",
                    )
                )

    results_df = pd.DataFrame(results)

    if results_df.empty:
        return results_df, "Inga resultat skapades."

    results_df = results_df.sort_values(
        by=["EdgeCraft Score", "Profit Factor", "Total Return"],
        ascending=False,
    ).reset_index(drop=True)

    report = generate_optimizer_report(results_df)

    return results_df, report


def generate_optimizer_report(results_df):
    if results_df is None or results_df.empty:
        return "Ingen optimeringsdata hittades."

    approved_df = results_df[results_df["Approved"] == True].copy()
    error_df = results_df[results_df["Error"].astype(str) != ""].copy()

    lines = []
    lines.append("=" * 60)
    lines.append("EDGECRAFT MARKET & TIMEFRAME OPTIMIZER")
    lines.append("=" * 60)
    lines.append("")
    lines.append(f"Totalt antal tester: {len(results_df)}")
    lines.append(f"Godkända tester: {len(approved_df)}")
    lines.append(f"Fel / ej testbara: {len(error_df)}")
    lines.append("")

    if not error_df.empty:
        lines.append("DIAGNOSTIK")
        lines.append("----------------------------")
        for _, row in error_df.head(10).iterrows():
            lines.append(f"{row['Market']} | {row['Timeframe']} | {row['Error']}")
        lines.append("")

    if approved_df.empty:
        lines.append("Ingen kombination klarade minsta antal trades.")
        lines.append("=" * 60)
        return "\n".join(lines)

    best = approved_df.iloc[0]

    lines.append("BÄSTA KOMBINATION")
    lines.append("----------------------------")
    lines.append(f"Strategi: {best['Strategy']}")
    lines.append(f"Marknad: {best['Market']}")
    lines.append(f"Timeframe: {best['Timeframe']}")
    lines.append(f"EdgeCraft Score: {best['EdgeCraft Score']}")
    lines.append(f"Profit Factor: {best['Profit Factor']}")
    lines.append(f"Winrate: {best['Winrate']}%")
    lines.append(f"Max Drawdown: {best['Max Drawdown']}%")
    lines.append(f"Trades: {int(best['Trades'])}")
    lines.append(f"Total Return: {best['Total Return']}%")
    lines.append("=" * 60)

    return "\n".join(lines)