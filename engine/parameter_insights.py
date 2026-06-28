# engine/parameter_insights.py
# EdgeCraft Quant Lab

import math
from typing import Any, Dict, List

import pandas as pd


NUMERIC_COLUMNS = [
    "EdgeCraft Score",
    "Profit Factor",
    "Winrate",
    "Max Drawdown",
    "Trades",
    "Total Return",
]


PARAMETER_COLUMNS = [
    "require_new_higher_high",
    "stop_type",
    "atr_multiple",
    "exit_days",
    "Exit Model",
]


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    text = str(value).strip().upper()
    return text in {"TRUE", "JA", "YES", "1"}


def _safe_mean(series: pd.Series) -> float:
    values = pd.to_numeric(series, errors="coerce").dropna()
    if values.empty:
        return 0.0
    return float(values.mean())


def _safe_median(series: pd.Series) -> float:
    values = pd.to_numeric(series, errors="coerce").dropna()
    if values.empty:
        return 0.0
    return float(values.median())


def _round(value: float, decimals: int = 2) -> float:
    try:
        if value is None or math.isnan(float(value)):
            return 0.0
        return round(float(value), decimals)
    except Exception:
        return 0.0


def _as_dataframe(records: Any) -> pd.DataFrame:
    if records is None:
        return pd.DataFrame()
    if isinstance(records, pd.DataFrame):
        return records.copy()
    if isinstance(records, list):
        return pd.DataFrame(records)
    return pd.DataFrame()


def summarize_group(df: pd.DataFrame) -> Dict[str, Any]:
    if df is None or df.empty:
        return {
            "count": 0,
            "approved": 0,
            "avg_score": 0,
            "median_score": 0,
            "avg_pf": 0,
            "avg_winrate": 0,
            "avg_drawdown": 0,
            "avg_trades": 0,
            "avg_return": 0,
        }

    approved = 0
    if "Approved" in df.columns:
        approved = int(df["Approved"].astype(bool).sum())

    return {
        "count": int(len(df)),
        "approved": approved,
        "avg_score": _round(_safe_mean(df.get("EdgeCraft Score", pd.Series(dtype=float))), 2),
        "median_score": _round(_safe_median(df.get("EdgeCraft Score", pd.Series(dtype=float))), 2),
        "avg_pf": _round(_safe_mean(df.get("Profit Factor", pd.Series(dtype=float))), 3),
        "avg_winrate": _round(_safe_mean(df.get("Winrate", pd.Series(dtype=float))), 2),
        "avg_drawdown": _round(_safe_mean(df.get("Max Drawdown", pd.Series(dtype=float))), 2),
        "avg_trades": _round(_safe_mean(df.get("Trades", pd.Series(dtype=float))), 1),
        "avg_return": _round(_safe_mean(df.get("Total Return", pd.Series(dtype=float))), 2),
    }


def compare_binary_parameter(records: Any, parameter: str) -> Dict[str, Any]:
    df = _as_dataframe(records)
    if df.empty or parameter not in df.columns:
        return {
            "status": "NO_DATA",
            "parameter": parameter,
            "message": f"Parametern {parameter} saknas i resultatet.",
        }

    df = df.copy()
    df[parameter] = df[parameter].map(_to_bool)

    false_df = df[df[parameter] == False].copy()
    true_df = df[df[parameter] == True].copy()

    if false_df.empty or true_df.empty:
        return {
            "status": "NO_COMPARISON",
            "parameter": parameter,
            "message": f"Det finns inte resultat för både True och False för {parameter}.",
            "false": summarize_group(false_df),
            "true": summarize_group(true_df),
        }

    false_summary = summarize_group(false_df)
    true_summary = summarize_group(true_df)

    score_delta = true_summary["avg_score"] - false_summary["avg_score"]
    pf_delta = true_summary["avg_pf"] - false_summary["avg_pf"]
    dd_delta = true_summary["avg_drawdown"] - false_summary["avg_drawdown"]
    approved_delta = true_summary["approved"] - false_summary["approved"]

    return {
        "status": "OK",
        "parameter": parameter,
        "false": false_summary,
        "true": true_summary,
        "score_delta": _round(score_delta, 2),
        "pf_delta": _round(pf_delta, 3),
        "drawdown_delta": _round(dd_delta, 2),
        "approved_delta": int(approved_delta),
    }


def build_hh_filter_verdict(records: Any) -> Dict[str, Any]:
    comparison = compare_binary_parameter(records, "require_new_higher_high")
    if comparison.get("status") != "OK":
        return {
            "status": comparison.get("status", "NO_DATA"),
            "recommendation": "UNKNOWN",
            "message": comparison.get("message", "Ingen HH-analys tillgänglig."),
            "comparison": comparison,
        }

    score_delta = comparison["score_delta"]
    pf_delta = comparison["pf_delta"]
    dd_delta = comparison["drawdown_delta"]
    approved_delta = comparison["approved_delta"]

    # HH=True is better only if it improves score/PF without increasing drawdown materially.
    if score_delta > 5 and pf_delta > 0 and dd_delta <= 3 and approved_delta >= 0:
        recommendation = "USE_HH_TRUE"
        message = "HH-filter verkar förbättra strategin. Rekommendation: använd HH = JA."
    elif score_delta < -5 or pf_delta < -0.05 or dd_delta > 5 or approved_delta < 0:
        recommendation = "USE_HH_FALSE"
        message = "HH-filter verkar försämra strategin. Rekommendation: använd HH = NEJ."
    else:
        recommendation = "NO_CLEAR_EDGE"
        message = "HH-filter ger ingen tydlig förbättring. Rekommendation: håll HH = NEJ tills vidare."

    return {
        "status": "OK",
        "recommendation": recommendation,
        "message": message,
        "comparison": comparison,
    }


def build_parameter_insights(records: Any) -> List[Dict[str, Any]]:
    df = _as_dataframe(records)
    if df.empty:
        return []

    insights: List[Dict[str, Any]] = []

    if "require_new_higher_high" in df.columns:
        comparison = compare_binary_parameter(df, "require_new_higher_high")
        if comparison.get("status") == "OK":
            false_summary = comparison["false"]
            true_summary = comparison["true"]
            best_value = "JA" if true_summary["avg_score"] > false_summary["avg_score"] else "NEJ"
            insights.append({
                "Parameter": "HH-filter",
                "Bäst": best_value,
                "HH=NEJ Avg Score": false_summary["avg_score"],
                "HH=JA Avg Score": true_summary["avg_score"],
                "PF diff JA-NEJ": comparison["pf_delta"],
                "DD diff JA-NEJ": comparison["drawdown_delta"],
                "Slutsats": "JA förbättrar" if best_value == "JA" else "NEJ är bättre",
            })

    for parameter in ["stop_type", "atr_multiple", "exit_days", "Exit Model"]:
        if parameter not in df.columns:
            continue

        grouped = []
        for value, group in df.groupby(parameter):
            summary = summarize_group(group)
            grouped.append({
                "value": value,
                "avg_score": summary["avg_score"],
                "avg_pf": summary["avg_pf"],
                "avg_drawdown": summary["avg_drawdown"],
                "approved": summary["approved"],
                "count": summary["count"],
            })

        if len(grouped) < 2:
            continue

        grouped = sorted(grouped, key=lambda x: (x["avg_score"], x["avg_pf"]), reverse=True)
        best = grouped[0]
        second = grouped[1]
        insights.append({
            "Parameter": parameter,
            "Bäst": best["value"],
            "Näst bäst": second["value"],
            "Bästa Avg Score": best["avg_score"],
            "Näst bästa Avg Score": second["avg_score"],
            "Bästa Avg PF": best["avg_pf"],
            "Bästa Avg DD": best["avg_drawdown"],
            "Slutsats": f"{best['value']} leder just nu",
        })

    return insights
