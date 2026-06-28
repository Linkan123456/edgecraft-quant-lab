from engine.core_backtest import run_strategy_backtest
from engine.walk_forward import run_walk_forward
from engine.monte_carlo import run_monte_carlo


def validate_strategy(
    data,
    strategy_name,
    initial_capital,
    parameters,
    market="",
    timeframe="",
    min_trades=100,
    min_profit_factor=1.3,
    max_drawdown_limit=25,
    min_total_return=0,
    simulations=1000
):
    backtest_result = run_strategy_backtest(
        data=data,
        strategy_name=strategy_name,
        initial_capital=initial_capital,
        parameters=parameters,
        market=market,
        timeframe=timeframe
    )

    stats = backtest_result.stats
    trades_df = backtest_result.trades

    checks = {}

    checks["Trades"] = stats["Trades"] >= min_trades
    checks["Profit Factor"] = stats["Profit Factor"] >= min_profit_factor
    checks["Total Return"] = stats["Total Return"] > min_total_return
    checks["Max Drawdown"] = abs(stats["Max Drawdown"]) <= max_drawdown_limit

    mc_df, mc_summary = run_monte_carlo(
        trades_df=trades_df,
        initial_capital=initial_capital,
        simulations=simulations
    )

    if mc_summary:
        checks["Monte Carlo Worst DD"] = abs(mc_summary["Worst Max Drawdown"]) <= max_drawdown_limit
        checks["Monte Carlo Median Return"] = mc_summary["Median Return"] > min_total_return
    else:
        checks["Monte Carlo Worst DD"] = False
        checks["Monte Carlo Median Return"] = False

    passed_checks = sum(checks.values())
    total_checks = len(checks)

    validation_score = round((passed_checks / total_checks) * 100, 2)

    approved = validation_score >= 70

    if validation_score >= 85:
        rating = "Stark kandidat"
    elif validation_score >= 70:
        rating = "Godkänd för vidare test"
    elif validation_score >= 50:
        rating = "Svag kandidat"
    else:
        rating = "Underkänd"

    return {
        "approved": approved,
        "rating": rating,
        "validation_score": validation_score,
        "checks": checks,
        "backtest_result": backtest_result,
        "monte_carlo_results": mc_df,
        "monte_carlo_summary": mc_summary
    }