# engine/ai_research_engine.py
# EdgeCraft Quant Lab v2 - AI Research Engine

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from data.downloader import load_market_data
from engine.backtester import run_backtest
from engine.scoring import calculate_edgecraft_score
from engine.statistics import calculate_statistics
from engine.strategy_runner import StrategyRunner
from engine.research_filters import professional_filter_library, ResearchFilter


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        if isinstance(value, float) and math.isnan(value):
            return default
        return float(value)
    except Exception:
        return default


def _parse_risk_reward(exit_model: Any, default: float = 3.0) -> float:
    text = str(exit_model or "").upper().replace(" ", "")
    if text.endswith("R"):
        return _safe_float(text.replace("R", ""), default)
    return default


def _best_exit_row(optimization_output: Dict[str, Any]) -> Dict[str, Any]:
    rows = optimization_output.get("exit_results") or optimization_output.get("top_candidates") or []
    df = pd.DataFrame(rows)
    if df.empty:
        best = optimization_output.get("best") or optimization_output.get("best_combination") or {}
        return best if isinstance(best, dict) else {}

    sort_cols = [c for c in ["EdgeCraft Score", "Profit Factor", "Total Return"] if c in df.columns]
    if sort_cols:
        df = df.sort_values(by=sort_cols, ascending=False).reset_index(drop=True)
    return df.iloc[0].to_dict()


def build_base_parameters(strategy_name: str, optimization_output: Dict[str, Any]) -> Dict[str, Any]:
    runner = StrategyRunner(strategy_name)
    params = runner.get_default_parameters().copy()
    best = _best_exit_row(optimization_output)

    for key, value in best.items():
        if key in params or key in {
            "ma_fast", "ma_slow", "ma_long", "pullback_min_days", "pullback_max_days",
            "near_high_pct", "volume_filter", "entry_trigger", "stop_type", "atr_period",
            "atr_multiple", "exit_days", "require_new_higher_high", "risk_reward",
        }:
            params[key] = value

    params["risk_reward"] = _parse_risk_reward(best.get("Exit Model"), params.get("risk_reward", 3))
    return params


def _apply_filter_to_signal_data(signal_data: pd.DataFrame, filter_item: ResearchFilter, market_df: Optional[pd.DataFrame]) -> pd.DataFrame:
    df = signal_data.copy()
    mask = filter_item.apply(df, market_df)
    mask = mask.reindex(df.index).fillna(False).astype(bool)
    df["BuySignal"] = df["BuySignal"].fillna(False).astype(bool) & mask
    df["ResearchFilter"] = filter_item.id
    return df


def _run_filtered_backtest(
    strategy_name: str,
    data: pd.DataFrame,
    market: str,
    timeframe: str,
    parameters: Dict[str, Any],
    filter_item: ResearchFilter,
    market_regime_df: Optional[pd.DataFrame],
    initial_capital: float,
    min_trades: int,
) -> Dict[str, Any]:
    runner = StrategyRunner(strategy_name)
    signal_data = runner.apply_signals(data=data.copy(), **parameters)
    filtered_signal_data = _apply_filter_to_signal_data(signal_data, filter_item, market_regime_df)

    result_df, trades_df = run_backtest(
        data=filtered_signal_data,
        initial_capital=initial_capital,
        parameters=parameters,
    )

    stats = calculate_statistics(
        df=result_df,
        trades_df=trades_df,
        initial_capital=initial_capital,
    )

    score = calculate_edgecraft_score(stats=stats, min_trades=min_trades)

    return {
        "Strategy": strategy_name,
        "Market": market,
        "Timeframe": timeframe,
        "Filter ID": filter_item.id,
        "Filter": filter_item.name,
        "Category": filter_item.category,
        "Description": filter_item.description,
        "EdgeCraft Score": score,
        "Profit Factor": stats.get("Profit Factor", 0),
        "Winrate": stats.get("Winrate", 0),
        "Max Drawdown": stats.get("Max Drawdown", 0),
        "Trades": stats.get("Trades", 0),
        "Total Return": stats.get("Total Return", 0),
        "Approved": stats.get("Trades", 0) >= min_trades and score > 0,
    }


def run_filter_lab(
    strategy_name: str,
    base_parameters: Dict[str, Any],
    markets: List[str],
    timeframe: str = "1d",
    start: str = "2015-01-01",
    end: Optional[str] = None,
    initial_capital: float = 100000,
    min_trades: int = 30,
    max_filters: Optional[int] = None,
) -> Dict[str, Any]:
    filters = professional_filter_library()
    if max_filters:
        filters = filters[: int(max_filters)]

    market_regime_df = None
    try:
        market_regime_df = load_market_data("SPY", start=start, end=end, interval=timeframe)
    except Exception:
        market_regime_df = None

    rows: List[Dict[str, Any]] = []
    errors: List[Dict[str, Any]] = []

    for market in markets:
        try:
            data = load_market_data(ticker=market, start=start, end=end, interval=timeframe)
            if data is None or data.empty:
                errors.append({"Market": market, "Error": "No data"})
                continue

            for filter_item in filters:
                try:
                    row = _run_filtered_backtest(
                        strategy_name=strategy_name,
                        data=data,
                        market=market,
                        timeframe=timeframe,
                        parameters=base_parameters,
                        filter_item=filter_item,
                        market_regime_df=market_regime_df,
                        initial_capital=initial_capital,
                        min_trades=min_trades,
                    )
                    rows.append(row)
                except Exception as e:
                    errors.append({"Market": market, "Filter": filter_item.id, "Error": str(e)})
        except Exception as e:
            errors.append({"Market": market, "Error": str(e)})

    results_df = pd.DataFrame(rows)
    if results_df.empty:
        return {
            "status": "NO_RESULTS",
            "results": [],
            "summary": [],
            "improvements": [],
            "declines": [],
            "best_recipe": {},
            "errors": errors,
        }

    summary = summarize_filter_lab(results_df)
    improvements, declines = classify_filter_impact(summary)
    best_recipe = build_trade_recipe(strategy_name, base_parameters, summary, improvements)

    return {
        "status": "OK",
        "results": results_df.sort_values(["EdgeCraft Score", "Profit Factor", "Total Return"], ascending=False).to_dict("records"),
        "summary": summary.to_dict("records"),
        "improvements": improvements,
        "declines": declines,
        "best_recipe": best_recipe,
        "errors": errors,
    }


def summarize_filter_lab(results_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    baseline = results_df[results_df["Filter ID"] == "NO_EXTRA_FILTER"].copy()
    baseline_score = _safe_float(baseline["EdgeCraft Score"].median() if not baseline.empty else 0)
    baseline_pf = _safe_float(baseline["Profit Factor"].median() if not baseline.empty else 0)
    baseline_dd = _safe_float(baseline["Max Drawdown"].median() if not baseline.empty else 999)

    for filter_id, group in results_df.groupby("Filter ID"):
        first = group.iloc[0]
        med_score = _safe_float(group["EdgeCraft Score"].median())
        med_pf = _safe_float(group["Profit Factor"].median())
        med_dd = _safe_float(group["Max Drawdown"].median())
        med_trades = _safe_float(group["Trades"].median())
        med_return = _safe_float(group["Total Return"].median())
        approved_count = int(group["Approved"].astype(bool).sum()) if "Approved" in group.columns else 0

        rows.append({
            "Filter ID": filter_id,
            "Filter": first.get("Filter", filter_id),
            "Category": first.get("Category", ""),
            "Tests": int(len(group)),
            "Approved": approved_count,
            "Median Score": round(med_score, 2),
            "Median PF": round(med_pf, 3),
            "Median DD": round(med_dd, 2),
            "Median Trades": round(med_trades, 1),
            "Median Return": round(med_return, 2),
            "Score Delta": round(med_score - baseline_score, 2),
            "PF Delta": round(med_pf - baseline_pf, 3),
            "DD Delta": round(med_dd - baseline_dd, 2),
        })

    return pd.DataFrame(rows).sort_values(["Score Delta", "PF Delta", "DD Delta"], ascending=[False, False, True]).reset_index(drop=True)


def classify_filter_impact(summary_df: pd.DataFrame) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    improvements = []
    declines = []

    if summary_df is None or summary_df.empty:
        return improvements, declines

    for _, row in summary_df.iterrows():
        if row.get("Filter ID") == "NO_EXTRA_FILTER":
            continue

        score_delta = _safe_float(row.get("Score Delta"))
        pf_delta = _safe_float(row.get("PF Delta"))
        dd_delta = _safe_float(row.get("DD Delta"))
        approved = int(row.get("Approved", 0))

        item = row.to_dict()
        if score_delta >= 5 and pf_delta >= 0 and dd_delta <= 3 and approved > 0:
            improvements.append(item)
        elif score_delta <= -5 or pf_delta < -0.15 or dd_delta > 5:
            declines.append(item)

    improvements = sorted(improvements, key=lambda x: _safe_float(x.get("Score Delta")), reverse=True)
    declines = sorted(declines, key=lambda x: _safe_float(x.get("Score Delta")))
    return improvements, declines


def build_trade_recipe(strategy_name: str, base_parameters: Dict[str, Any], summary_df: pd.DataFrame, improvements: List[Dict[str, Any]]) -> Dict[str, Any]:
    selected_filters = [x.get("Filter") for x in improvements[:3]]

    return {
        "Strategy": strategy_name,
        "Timeframe": "Daily",
        "Entry": base_parameters.get("entry_trigger", "BreakPreviousHigh"),
        "Trend": f"MA{base_parameters.get('ma_fast', 20)} > MA{base_parameters.get('ma_slow', 50)} > MA{base_parameters.get('ma_long', 200)}",
        "Stop": base_parameters.get("stop_type", "-"),
        "ATR Multiple": base_parameters.get("atr_multiple", "-"),
        "Exit": f"{base_parameters.get('risk_reward', '-') }R / {base_parameters.get('exit_days', '-') } dagar",
        "HH Filter": "JA" if base_parameters.get("require_new_higher_high") else "NEJ",
        "Recommended Filters": selected_filters,
    }


def run_ai_research_engine(
    strategy_name: str,
    optimization_output: Dict[str, Any],
    markets: List[str],
    timeframe: str = "1d",
    start: str = "2015-01-01",
    end: Optional[str] = None,
    initial_capital: float = 100000,
    min_trades: int = 30,
) -> Dict[str, Any]:
    base_parameters = build_base_parameters(strategy_name, optimization_output)
    return run_filter_lab(
        strategy_name=strategy_name,
        base_parameters=base_parameters,
        markets=markets,
        timeframe=timeframe,
        start=start,
        end=end,
        initial_capital=initial_capital,
        min_trades=min_trades,
    )
