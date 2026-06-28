# engine/optimization_pipeline.py
# EdgeCraft Quant Lab

from datetime import datetime

from engine.market_timeframe_optimizer import run_market_timeframe_optimizer
from engine.research_pipeline import get_top_candidates, generate_research_summary
from engine.exit_research import run_exit_research
from engine.robustness import run_robustness_analysis
from engine.walk_forward_runner import run_walk_forward_for_candidate
from engine.monte_carlo_runner import run_monte_carlo_for_candidate
from engine.paper_trading import run_paper_trading_check, generate_paper_trading_report
from engine.strategy_runner import StrategyRunner


def _safe_get(row, key, default=0):
    if isinstance(row, dict):
        return row.get(key, default)
    return default


def _to_float(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return default


def _to_int(value, default=0):
    try:
        return int(float(value))
    except Exception:
        return default


def _decide_conclusion(
    best_row,
    robustness_report=None,
    walk_forward_report="",
    monte_carlo_summary=None,
    min_trades=30,
):
    trades = _to_int(_safe_get(best_row, "Trades", 0))
    score = _to_float(_safe_get(best_row, "EdgeCraft Score", 0))
    pf = _to_float(_safe_get(best_row, "Profit Factor", 0))
    winrate = _to_float(_safe_get(best_row, "Winrate", 0))
    max_dd = abs(_to_float(_safe_get(best_row, "Max Drawdown", 999)))

    # Hard safety gate: invalid candidates can never become interesting/ready.
    if trades < min_trades or score <= 0 or pf <= 0:
        return "NOT_READY"

    is_robust = False
    if isinstance(robustness_report, dict):
        is_robust = robustness_report.get("is_robust", False)

    wf_green = isinstance(walk_forward_report, str) and "GRÖN" in walk_forward_report

    mc_score = 0
    mc_green = False
    if isinstance(monte_carlo_summary, dict):
        mc_score = _to_float(monte_carlo_summary.get("Monte Carlo Score", 0))
        mc_green = mc_score >= 70

    if (
        pf >= 1.6
        and winrate >= 50
        and max_dd <= 25
        and trades >= 50
        and is_robust
        and wf_green
        and mc_green
    ):
        return "ALGO_READY_CANDIDATE"

    if pf >= 1.25:
        return "NEEDS_MORE_TESTING"

    return "NOT_READY"


def _assessment(conclusion):
    if conclusion == "ALGO_READY_CANDIDATE":
        return "Strategin visar stark edge och klarar Screening, Exit Research, Robustness, Walk Forward och Monte Carlo."

    if conclusion == "NEEDS_MORE_TESTING":
        return "Strategin är intressant men behöver mer research innan den används live."

    return "Strategin är inte redo i nuvarande form."


def _build_best_combination(row):
    if not isinstance(row, dict):
        return None

    return {
        "market": _safe_get(row, "Market", ""),
        "timeframe": _safe_get(row, "Timeframe", ""),
        "score": _safe_get(row, "EdgeCraft Score", 0),
        "profit_factor": _safe_get(row, "Profit Factor", 0),
        "winrate": _safe_get(row, "Winrate", 0),
        "trades": _safe_get(row, "Trades", 0),
        "max_drawdown": _safe_get(row, "Max Drawdown", 0),
        "return": _safe_get(row, "Total Return", 0),
        "exit_model": _safe_get(row, "Exit Model", ""),
        "stop_type": _safe_get(row, "stop_type", ""),
        "atr_multiple": _safe_get(row, "atr_multiple", ""),
        "exit_days": _safe_get(row, "exit_days", ""),
        "require_new_higher_high": _safe_get(row, "require_new_higher_high", False),
    }


def _validate_candidate(row, min_trades=30):
    if not isinstance(row, dict) or not row:
        return False, "Kandidaten stoppades: ingen giltig kandidat hittades."

    trades = _to_int(_safe_get(row, "Trades", 0))
    score = _to_float(_safe_get(row, "EdgeCraft Score", 0))
    pf = _to_float(_safe_get(row, "Profit Factor", 0))

    if trades < min_trades:
        return False, f"Kandidaten stoppades: endast {trades} trades. Minimikravet är {min_trades}."

    if score <= 0:
        return False, "Kandidaten stoppades: EdgeCraft Score är 0 eller lägre."

    if pf <= 0:
        return False, "Kandidaten stoppades: Profit Factor är 0 eller ogiltig."

    return True, ""


def _blocked_pipeline_result(
    reason,
    best_row,
    results_df,
    top_df,
    exit_df,
    research_summary,
    optimizer_report,
    exit_summary,
):
    best_combination = _build_best_combination(best_row)

    return {
        "conclusion": "NOT_READY",
        "status": "NOT_READY",
        "verdict": "NOT_READY",
        "final_decision": "NOT_READY",

        "best_combination": best_combination,
        "best_result": best_combination,
        "best": best_combination,

        "short_assessment": reason,
        "assessment": reason,
        "summary": reason,

        "results": [] if results_df is None else results_df.to_dict("records"),
        "top_candidates": [] if top_df is None else top_df.to_dict("records"),
        "exit_results": [] if exit_df is None else exit_df.to_dict("records"),

        "robustness_results": [],
        "walk_forward_results": [],
        "monte_carlo_results": [],

        "research_summary": research_summary,
        "optimizer_report": optimizer_report,
        "exit_summary": exit_summary,

        "robustness_report": {
            "status": "BLOCKED",
            "message": reason,
            "is_robust": False,
            "robust_rows": 0,
            "robust_ratio": 0,
        },
        "walk_forward_report": f"BLOCKED: {reason}",
        "monte_carlo_summary": {
            "Traffic Light": "🔴 Blocked",
            "Monte Carlo Score": 0,
            "Profit Probability %": 0,
            "Worst Max Drawdown %": 0,
        },
        "monte_carlo_report": f"BLOCKED: {reason}",
        "paper_trading_snapshot": {
            "status": "BLOCKED",
            "in_position": False,
            "signal": None,
            "levels": {},
        },
        "paper_trading_report": f"BLOCKED: {reason}",

        "screened_count": 0 if results_df is None else len(results_df),
        "approved_count": 0,
    }


def _no_data_result(optimizer_report):
    return {
        "conclusion": "NOT_READY",
        "status": "NOT_READY",
        "verdict": "NOT_READY",
        "final_decision": "NOT_READY",
        "best_combination": None,
        "best_result": None,
        "best": None,
        "short_assessment": "Inga resultat kunde tas fram.",
        "assessment": "Inga resultat kunde tas fram.",
        "summary": "Inga resultat kunde tas fram.",
        "results": [],
        "top_candidates": [],
        "exit_results": [],
        "robustness_results": [],
        "walk_forward_results": [],
        "monte_carlo_results": [],
        "monte_carlo_summary": {
            "Traffic Light": "🔴 No data",
            "Monte Carlo Score": 0,
        },
        "paper_trading_snapshot": {
            "status": "NO_DATA",
            "in_position": False,
            "signal": None,
            "levels": {},
        },
        "research_summary": optimizer_report,
        "optimizer_report": optimizer_report,
        "exit_summary": "",
        "robustness_report": {
            "status": "NO_DATA",
            "message": "Ingen data fanns att analysera i Robustness.",
            "is_robust": False,
        },
        "walk_forward_report": "Ingen Walk Forward-data.",
        "monte_carlo_report": "Ingen Monte Carlo-data.",
        "paper_trading_report": "Ingen Paper Trading-data.",
        "screened_count": 0,
        "approved_count": 0,
    }


def run_full_optimization_pipeline(
    strategy_name,
    parameter_grid=None,
    start="2015-01-01",
    end=None,
    initial_capital=100000,
    markets=None,
    timeframes=None,
    top_n=5,
    min_trades=30,
    simulations=1000,
    **kwargs,
):
    if end is None:
        end = datetime.today().strftime("%Y-%m-%d")

    if parameter_grid is None:
        runner = StrategyRunner(strategy_name)
        parameter_grid = runner.get_parameter_grid()

    print("\n===== EDGECRAFT PARAMETER GRID =====")
    print(parameter_grid)
    print("====================================\n")

    results_df, optimizer_report = run_market_timeframe_optimizer(
        strategy_name=strategy_name,
        parameter_grid=parameter_grid,
        start=start,
        end=end,
        initial_capital=initial_capital,
        min_trades=min_trades,
        markets=markets,
        timeframes=timeframes,
    )

    if results_df is None or results_df.empty:
        return _no_data_result(optimizer_report)

    top_df = get_top_candidates(
        research_df=results_df,
        top_n=top_n,
        min_trades=min_trades,
    )

    if top_df is None or top_df.empty:
        top_df = results_df.head(top_n).copy()

    try:
        research_summary = generate_research_summary(
            research_df=results_df,
            top_df=top_df,
        )
    except Exception:
        research_summary = optimizer_report

    exit_df, exit_summary = run_exit_research(
        strategy_name=strategy_name,
        top_candidates=top_df.to_dict("records"),
        start=start,
        end=end,
        initial_capital=initial_capital,
        min_trades=min_trades,
    )

    if exit_df is not None and not exit_df.empty:
        best_row = exit_df.iloc[0].to_dict()
    else:
        best_row = top_df.iloc[0].to_dict()

    is_valid, invalid_reason = _validate_candidate(best_row, min_trades=min_trades)
    if not is_valid:
        return _blocked_pipeline_result(
            reason=invalid_reason,
            best_row=best_row,
            results_df=results_df,
            top_df=top_df,
            exit_df=exit_df,
            research_summary=research_summary,
            optimizer_report=optimizer_report,
            exit_summary=exit_summary,
        )

    robustness_source_df = exit_df if exit_df is not None and not exit_df.empty else top_df
    robustness_df, robustness_report = run_robustness_analysis(
        research_df=robustness_source_df,
        score_column="EdgeCraft Score",
        min_score_ratio=0.80,
    )

    walk_forward_df, walk_forward_report = run_walk_forward_for_candidate(
        strategy_name=strategy_name,
        candidate=best_row,
        start=start,
        end=end,
        initial_capital=initial_capital,
    )

    monte_carlo_df, monte_carlo_summary, monte_carlo_report = run_monte_carlo_for_candidate(
        strategy_name=strategy_name,
        candidate=best_row,
        start=start,
        end=end,
        initial_capital=initial_capital,
        simulations=simulations,
    )

    paper_trading_snapshot = run_paper_trading_check(
        strategy_name=strategy_name,
        candidate=best_row,
        start=start,
        end=end,
        initial_capital=initial_capital,
    )

    paper_trading_report = generate_paper_trading_report(paper_trading_snapshot)

    best_combination = _build_best_combination(best_row)

    conclusion = _decide_conclusion(
        best_row=best_row,
        robustness_report=robustness_report,
        walk_forward_report=walk_forward_report,
        monte_carlo_summary=monte_carlo_summary,
        min_trades=min_trades,
    )

    assessment = _assessment(conclusion)

    return {
        "conclusion": conclusion,
        "status": conclusion,
        "verdict": conclusion,
        "final_decision": conclusion,

        "best_combination": best_combination,
        "best_result": best_combination,
        "best": best_combination,

        "short_assessment": assessment,
        "assessment": assessment,
        "summary": assessment,

        "results": results_df.to_dict("records"),
        "top_candidates": top_df.to_dict("records"),
        "exit_results": [] if exit_df is None else exit_df.to_dict("records"),
        "robustness_results": [] if robustness_df is None else robustness_df.to_dict("records"),
        "walk_forward_results": [] if walk_forward_df is None else walk_forward_df.to_dict("records"),
        "monte_carlo_results": [] if monte_carlo_df is None else monte_carlo_df.to_dict("records"),

        "research_summary": research_summary,
        "optimizer_report": optimizer_report,
        "exit_summary": exit_summary,
        "robustness_report": robustness_report,
        "walk_forward_report": walk_forward_report,
        "monte_carlo_summary": monte_carlo_summary,
        "monte_carlo_report": monte_carlo_report,
        "paper_trading_snapshot": paper_trading_snapshot,
        "paper_trading_report": paper_trading_report,

        "screened_count": len(results_df),
        "approved_count": len(top_df),
    }
