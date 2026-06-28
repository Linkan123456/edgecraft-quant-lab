# engine/confidence.py
# EdgeCraft Quant Lab v0.60


def calculate_confidence_score(
    research_score=0,
    walk_forward_score=0,
    monte_carlo_score=0
):
    score = (
        research_score * 0.35
        + walk_forward_score * 0.40
        + monte_carlo_score * 0.25
    )

    return round(score, 2)


def get_confidence_label(score):
    if score >= 75:
        return "HÖG KONFIDENS"
    if score >= 60:
        return "MEDEL KONFIDENS"
    if score >= 45:
        return "LÅG KONFIDENS"
    return "EJ GODKÄND"


def get_confidence_traffic_light(score):
    if score >= 75:
        return "GRÖN - Strategin är intressant för vidare verifiering"
    if score >= 60:
        return "GUL - Strategin behöver mer testning"
    if score >= 45:
        return "ORANGE - Svag edge, hög osäkerhet"
    return "RÖD - Ej robust nog"


def generate_confidence_report(
    research_score=0,
    walk_forward_score=0,
    monte_carlo_score=0
):
    confidence_score = calculate_confidence_score(
        research_score=research_score,
        walk_forward_score=walk_forward_score,
        monte_carlo_score=monte_carlo_score
    )

    confidence_label = get_confidence_label(confidence_score)
    traffic_light = get_confidence_traffic_light(confidence_score)

    lines = []

    lines.append("=" * 60)
    lines.append("EDGECRAFT CONFIDENCE REPORT v0.60")
    lines.append("=" * 60)
    lines.append("")
    lines.append(f"Research Score: {research_score}")
    lines.append(f"Walk Forward Score: {walk_forward_score}")
    lines.append(f"Monte Carlo Score: {monte_carlo_score}")
    lines.append("")
    lines.append(f"EdgeCraft Confidence Score: {confidence_score}")
    lines.append(f"Bedömning: {confidence_label}")
    lines.append(f"Trafikljus: {traffic_light}")
    lines.append("")
    lines.append("SLUTSATS")
    lines.append("----------------------------")

    if confidence_score >= 75:
        lines.append("Strategin visar stark samlad robusthet.")
        lines.append("Nästa steg är djupare out-of-sample-test och live paper trading.")
    elif confidence_score >= 60:
        lines.append("Strategin är intressant men behöver stärkas.")
        lines.append("Nästa steg är fler marknader, fler timeframes och Monte Carlo-verifiering.")
    elif confidence_score >= 45:
        lines.append("Strategin visar viss potential men är osäker.")
        lines.append("Risken är att edgen är för svag eller marknadsberoende.")
    else:
        lines.append("Strategin är inte tillräckligt robust.")
        lines.append("Den bör inte användas som live-strategi i nuvarande form.")

    lines.append("")
    lines.append("Nästa steg: skapa en Dashboard-sida som visar Confidence Score.")
    lines.append("=" * 60)

    return "\n".join(lines)