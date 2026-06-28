# engine/core_backtest.py
# EdgeCraft Quant Lab

from engine.strategy_runner import StrategyRunner
from engine.backtester import run_backtest
from engine.statistics import calculate_statistics
from engine.result import BacktestResult


def run_strategy_backtest(
    data,
    strategy_name,
    initial_capital=100000,
    parameters=None,
    market="",
    timeframe="",
):
    if parameters is None:
        parameters = {}

    runner = StrategyRunner(strategy_name)

    signal_data = runner.apply_signals(
        data=data.copy(),
        **parameters,
    )

    result_df, trades_df = run_backtest(
        data=signal_data,
        initial_capital=initial_capital,
        parameters=parameters,
    )

    stats = calculate_statistics(
        df=result_df,
        trades_df=trades_df,
        initial_capital=initial_capital,
    )

    return BacktestResult(
        strategy=strategy_name,
        parameters=parameters,
        equity=result_df,
        trades=trades_df,
        stats=stats,
        market=market,
        timeframe=timeframe,
    )