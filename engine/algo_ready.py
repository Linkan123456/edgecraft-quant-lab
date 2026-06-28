# engine/algo_ready.py
# EdgeCraft Quant Lab


def _to_float(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return default


def calculate_algo_ready_score(
    best_combination,
    robustness_report=None,
    walk_forward_report="",
    monte_carlo_summary=None,
):
    if best_combination is None:
        return {
            "score": 0,
            "status": "NOT_READY",
            "traffic_light": "RÖD",
            "message": "Ingen bästa kombination finns att bedöma.",
            "components": {},
        }

    pf = _to_float(best_combination.get("profit_factor", 0))
    winrate = _to_float(best_combination.get("winrate", 0))
    trades = _to_float(best_combination.get("trades", 0))
    max_dd = abs(_to_float(best_combination.get("max_drawdown", 999)))

    screening_score = 0

    if pf >= 2.0:
        screening_score += 30
    elif pf >= 1.6:
        screening_score += 24
    elif pf >= 1.25:
        screening_score += 16

    if winrate >= 65:
        screening_score += 20
    elif winrate >= 55:
        screening_score += 15
    elif winrate >= 50:
        screening_score += 10

    if trades >= 80:
        screening_score += 20
    elif trades >= 50:
        screening_score += 15
    elif trades >= 30:
        screening_score += 10

    if max_dd <= 10:
        screening_score += 20
    elif max_dd <= 20:
        screening_score += 15
    elif max_dd <= 30:
        screening_score += 8

    screening_score = min(100, screening_score)

    robustness_score = 0
    if isinstance(robustness_report, dict):
        robust_ratio = _to_float(robustness_report.get("robust_ratio", 0))
        is_robust = robustness_report.get("is_robust", False)

        robustness_score = min(100, robust_ratio * 100)

        if is_robust:
            robustness_score = max(robustness_score, 60)

    walk_forward_score = 0
    if isinstance(walk_forward_report, str):
        if "Walk Forward Score:" in walk_forward_report:
            try:
                part = walk_forward_report.split("Walk Forward Score:")[1]
                walk_forward_score = _to_float(part.splitlines()[0].strip())
            except Exception:
                walk_forward_score = 0

        if "GRÖN" in walk_forward_report:
            walk_forward_score = max(walk_forward_score, 70)
        elif "GUL" in walk_forward_report:
            walk_forward_score = max(walk_forward_score, 50)

    monte_carlo_score = 0
    if isinstance(monte_carlo_summary, dict):
        monte_carlo_score = _to_float(monte_carlo_summary.get("Monte Carlo Score", 0))

    total_score = (
        screening_score * 0.25
        + robustness_score * 0.20
        + walk_forward_score * 0.30
        + monte_carlo_score * 0.25
    )

    total_score = round(total_score, 2)

    if total_score >= 75 and monte_carlo_score >= 70 and walk_forward_score >= 70:
        status = "ALGO_READY"
        traffic_light = "GRÖN"
        message = "Strategin klarar helhetskraven och kan gå vidare till live/paper trading-fas."
    elif total_score >= 55:
        status = "NEEDS_MORE_TESTING"
        traffic_light = "GUL"
        message = "Strategin är lovande men behöver mer testning innan den används live."
    else:
        status = "NOT_READY"
        traffic_light = "RÖD"
        message = "Strategin är inte tillräckligt robust i nuvarande form."

    return {
        "score": total_score,
        "status": status,
        "traffic_light": traffic_light,
        "message": message,
        "components": {
            "screening_score": round(screening_score, 2),
            "robustness_score": round(robustness_score, 2),
            "walk_forward_score": round(walk_forward_score, 2),
            "monte_carlo_score": round(monte_carlo_score, 2),
        },
    }