# engine/scoring.py
# EdgeCraft Quant Lab v0.48


PF_SCORE_CAP = 5.0


def calculate_edgecraft_score(stats, min_trades=50):
    trades = stats.get("Trades", 0)
    profit_factor = stats.get("Profit Factor", 0)
    winrate = stats.get("Winrate", 0)
    total_return = stats.get("Total Return", 0)
    max_drawdown = stats.get("Max Drawdown", 0)

    if trades < min_trades:
        return 0

    safe_profit_factor = min(float(profit_factor), PF_SCORE_CAP)

    score = (
        (safe_profit_factor * 30)
        + (winrate * 0.4)
        + (total_return * 0.2)
        - abs(max_drawdown * 0.8)
    )

    return round(score, 2)


def calculate_walk_forward_score(stats, min_trades=5):
    return calculate_edgecraft_score(
        stats=stats,
        min_trades=min_trades
    )


def calculate_monte_carlo_score(summary):
    if summary is None or len(summary) == 0:
        return 0

    profit_probability = summary.get("Profit Probability %", 0)
    median_return = summary.get("Median Return %", 0)
    worst_drawdown = summary.get("Worst Max Drawdown %", 0)

    score = (
        (profit_probability * 0.5)
        + (median_return * 0.8)
        - (abs(worst_drawdown) * 0.7)
    )

    return round(max(0, min(100, score)), 2)


def get_score_label(score):
    if score >= 80:
        return "Mycket stark"
    if score >= 65:
        return "Stark"
    if score >= 50:
        return "Intressant men osäker"
    if score >= 35:
        return "Svag"
    return "Ej robust"


def get_traffic_light(score):
    if score >= 70:
        return "GRÖN - Robust"
    if score >= 50:
        return "GUL - Osäker men intressant"
    return "RÖD - Ej robust"