def generate_improvement_advice(best):
    advice = []

    pf = float(best.get("Profit Factor", 0))
    wr = float(best.get("Winrate", best.get("Win Rate", 0)))
    dd = float(best.get("Max Drawdown", 0))
    trades = int(best.get("Trades", 0))

    if pf < 2:
        advice.append("Testa fler trendfilter (EMA100 / EMA200).")

    if wr < 55:
        advice.append("Prova striktare entry-filter.")

    if dd > 20:
        advice.append("Testa tajtare Stop Loss eller tidigare exit.")

    if trades < 100:
        advice.append("Testa fler marknader och längre historik.")

    if not advice:
        advice.append("Strategin ser balanserad ut. Fokusera på robusthetstester.")

    return advice