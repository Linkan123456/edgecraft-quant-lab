# engine/algo_readiness.py
# EdgeCraft Quant Lab v0.65


def calculate_algo_readiness_score(
    edgecraft_score=0,
    profit_factor=0,
    trades=0,
    max_drawdown=0,
    market_rank_strength=0,
    timeframe_rank_strength=0
):
    score = 0

    score += min(edgecraft_score, 100) * 0.35

    if profit_factor >= 2.0:
        score += 20
    elif profit_factor >= 1.5:
        score += 15
    elif profit_factor >= 1.2:
        score += 10
    elif profit_factor > 1.0:
        score += 5

    if trades >= 200:
        score += 15
    elif trades >= 100:
        score += 10
    elif trades >= 50:
        score += 5

    if max_drawdown <= 10:
        score += 15
    elif max_drawdown <= 20:
        score += 10
    elif max_drawdown <= 30:
        score += 5

    score += market_rank_strength * 0.075
    score += timeframe_rank_strength * 0.075

    return round(min(score, 100), 2)


def get_algo_readiness_label(score):
    if score >= 80:
        return "REDO FÖR PAPER TRADING"
    if score >= 65:
        return "INTRESSANT - KRÄVER MER TEST"
    if score >= 50:
        return "SVAG EDGE - OSÄKER"
    return "EJ REDO"


def generate_algo_readiness_report(best_row):
    if best_row is None:
        return "Ingen bästa kombination hittades."

    edgecraft_score = float(best_row.get("EdgeCraft Score", 0))
    profit_factor = float(best_row.get("Profit Factor", 0))
    trades = int(best_row.get("Trades", 0))
    max_drawdown = float(best_row.get("Max Drawdown", 0))

    market_rank_strength = float(best_row.get("Market Strength", 0))
    timeframe_rank_strength = float(best_row.get("Timeframe Strength", 0))

    algo_score = calculate_algo_readiness_score(
        edgecraft_score=edgecraft_score,
        profit_factor=profit_factor,
        trades=trades,
        max_drawdown=max_drawdown,
        market_rank_strength=market_rank_strength,
        timeframe_rank_strength=timeframe_rank_strength
    )

    label = get_algo_readiness_label(algo_score)

    lines = []

    lines.append("=" * 60)
    lines.append("EDGECRAFT ALGO READINESS REPORT v0.65")
    lines.append("=" * 60)
    lines.append("")
    lines.append(f"Strategi: {best_row.get('Strategy', '')}")
    lines.append(f"Marknad: {best_row.get('Market', '')}")
    lines.append(f"Timeframe: {best_row.get('Timeframe', '')}")
    lines.append("")
    lines.append(f"EdgeCraft Score: {edgecraft_score}")
    lines.append(f"Profit Factor: {profit_factor}")
    lines.append(f"Trades: {trades}")
    lines.append(f"Max Drawdown: {max_drawdown}%")
    lines.append("")
    lines.append(f"Algo Readiness Score: {algo_score}")
    lines.append(f"Bedömning: {label}")
    lines.append("")
    lines.append("SLUTSATS")
    lines.append("----------------------------")

    if algo_score >= 80:
        lines.append("Strategin är tillräckligt intressant för paper trading.")
        lines.append("Nästa steg är Walk Forward, Monte Carlo och live-liknande test.")
    elif algo_score >= 65:
        lines.append("Strategin har potential men behöver mer verifiering.")
        lines.append("Acceptera den inte som algo ännu.")
    elif algo_score >= 50:
        lines.append("Strategin visar viss edge men är för osäker.")
        lines.append("Den behöver förbättras eller testas på fler marknader.")
    else:
        lines.append("Strategin är inte redo för algo.")
        lines.append("Resultatet är för svagt eller för osäkert.")

    lines.append("=" * 60)

    return "\n".join(lines)