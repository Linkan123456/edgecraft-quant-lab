# engine/monte_carlo_runner.py
# EdgeCraft Quant Lab

from data.downloader import load_market_data
from engine.core_backtest import run_strategy_backtest
from engine.monte_carlo import run_monte_carlo_simulation, generate_monte_carlo_report


def run_monte_carlo_for_candidate(
    strategy_name,
    candidate,
    start="2015-01-01",
    end=None,
    initial_capital=100000,
    simulations=1000,
):
    if candidate is None:
        return None, {}, "Ingen kandidat skickades till Monte Carlo."

    market = candidate.get("Market") or candidate.get("market")
    timeframe = candidate.get("Timeframe") or candidate.get("timeframe")

    if not market or not timeframe:
        return None, {}, "Kandidaten saknar Market eller Timeframe."

    parameters = {}

    exit_model = candidate.get("Exit Model") or candidate.get("exit_model")

    if exit_model:
        try:
            parameters["risk_reward"] = int(str(exit_model).replace("R", "").strip())
        except Exception:
            pass

    data = load_market_data(
        ticker=market,
        start=start,
        end=end,
        interval=timeframe,
    )

    if data is None or data.empty:
        return None, {}, f"Ingen data hittades för {market} {timeframe}."

    result = run_strategy_backtest(
        data=data,
        strategy_name=strategy_name,
        initial_capital=initial_capital,
        parameters=parameters,
        market=market,
        timeframe=timeframe,
    )

    if result is None:
        return None, {}, "Backtest gav inget resultat."

    trades_df = getattr(result, "trades", None)

    if trades_df is None or trades_df.empty:
        return None, {}, "Inga trades fanns för Monte Carlo."

    monte_carlo_df, monte_carlo_summary = run_monte_carlo_simulation(
        trades_df=trades_df,
        initial_capital=initial_capital,
        simulations=simulations,
    )

    monte_carlo_report = generate_monte_carlo_report(monte_carlo_summary)

    return monte_carlo_df, monte_carlo_summary, monte_carlo_report