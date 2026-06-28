import pandas as pd


MIN_ROBUSTNESS_RATIO = 0.10
MIN_TRADES_SWING = 50
MIN_TRADES_INTRADAY = 200
MIN_PROFIT_FACTOR = 1.5
MAX_DRAWDOWN_LIMIT = 25.0


def safe_float(value, default=0.0):
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def get_value(source, keys, default=None):
    if source is None:
        return default

    for key in keys:
        if isinstance(source, dict) and key in source:
            return source.get(key)

        if hasattr(source, "get"):
            try:
                value = source.get(key)
                if value is not None:
                    return value
            except Exception:
                pass

    return default


def get_trade_requirement(strategy_dna):
    style = str(strategy_dna.get("best_trading_style", "")).lower()

    if "intradag" in style:
        return MIN_TRADES_INTRADAY

    return MIN_TRADES_SWING


def classify_status(score):
    if score >= 85:
        return "READY_FOR_LIVE_TEST"

    if score >= 70:
        return "STRONG_CANDIDATE"

    if score >= 55:
        return "NEEDS_MORE_TESTING"

    return "REJECT"


def build_recommendation_text(status, strategy_dna, reasons):
    best_market = strategy_dna.get("best_asset_class", "Okänd")
    best_timeframe = strategy_dna.get("best_timeframe", "Okänd")
    best_style = strategy_dna.get("best_trading_style", "Okänd")

    if status == "READY_FOR_LIVE_TEST":
        return (
            f"Strategin är tillräckligt stark för live-test i liten skala. "
            f"Den passar bäst för {best_market}, {best_timeframe}, {best_style}."
        )

    if status == "STRONG_CANDIDATE":
        return (
            f"Strategin är en stark kandidat men bör verifieras mer innan riktig handel. "
            f"Bäst område verkar vara {best_market}, {best_timeframe}, {best_style}."
        )

    if status == "NEEDS_MORE_TESTING":
        return (
            f"Strategin är intressant men inte redo. "
            f"EdgeCraft bör försöka förbättra den innan den används."
        )

    reason_text = ", ".join(reasons) if reasons else "för svaga resultat"
    return f"Strategin ska inte användas ännu. Orsak: {reason_text}."


def run_qualification_engine(
    best,
    strategy_dna=None,
    robustness_report=None,
    walk_forward_report="",
    monte_carlo_report="",
    algo_report="",
):
    if best is None:
        return {
            "status": "REJECT",
            "score": 0,
            "recommendation": "Ingen bästa kombination hittades.",
            "reasons": ["Ingen bästa kombination hittades."],
        }

    if strategy_dna is None:
        strategy_dna = {}

    reasons = []
    score = 100

    trades = safe_float(get_value(best, ["Trades"], 0))
    profit_factor = safe_float(get_value(best, ["Profit Factor"], 0))
    max_drawdown = safe_float(get_value(best, ["Max Drawdown"], 999))
    winrate = safe_float(get_value(best, ["Winrate", "Win Rate"], 0))

    min_trades = get_trade_requirement(strategy_dna)

    if trades < min_trades:
        score -= 25
        reasons.append(f"för få trades ({int(trades)} av minst {min_trades})")

    if profit_factor < MIN_PROFIT_FACTOR:
        score -= 20
        reasons.append(f"för låg Profit Factor ({profit_factor})")

    if max_drawdown > MAX_DRAWDOWN_LIMIT:
        score -= 20
        reasons.append(f"för hög drawdown ({max_drawdown}%)")

    robustness_ratio = None
    is_robust = False

    if isinstance(robustness_report, dict):
        robustness_ratio = safe_float(robustness_report.get("robust_ratio"), None)
        is_robust = bool(robustness_report.get("is_robust", False))

    if robustness_ratio is None:
        score -= 20
        reasons.append("robustness ratio saknas")
    elif robustness_ratio < MIN_ROBUSTNESS_RATIO:
        score -= 30
        reasons.append(f"för låg robustness ratio ({robustness_ratio})")

    wf_text = str(walk_forward_report).lower()
    mc_text = str(monte_carlo_report).lower()
    algo_text = str(algo_report).lower()

    if "röd" in wf_text or "red" in wf_text:
        score -= 20
        reasons.append("Walk Forward underkänd")

    if "röd" in mc_text or "red" in mc_text:
        score -= 20
        reasons.append("Monte Carlo underkänd")

    if "kräver mer test" in algo_text or "intressant" in algo_text:
        score -= 10
        reasons.append("Algo Readiness kräver mer test")

    score = max(0, min(100, round(score, 2)))
    status = classify_status(score)

    recommendation = build_recommendation_text(
        status=status,
        strategy_dna=strategy_dna,
        reasons=reasons,
    )

    return {
        "status": status,
        "score": score,
        "recommendation": recommendation,
        "reasons": reasons,
        "metrics": {
            "trades": trades,
            "min_trades": min_trades,
            "profit_factor": profit_factor,
            "winrate": winrate,
            "max_drawdown": max_drawdown,
            "robustness_ratio": robustness_ratio,
            "is_robust": is_robust,
        },
    }