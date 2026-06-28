# ============================================================
# EdgeCraft Quant Lab
# Version: v0.32
# File: engine/research_engine.py
# Purpose: AI Research Report
# ============================================================


def generate_research_report(df):
    report = []

    report.append("=" * 60)
    report.append("EDGECRAFT AI RESEARCH REPORT v0.32")
    report.append("=" * 60)
    report.append("")

    if df is None or df.empty:
        report.append("Ingen experimentdata hittades.")
        return "\n".join(report)

    report.append(f"Antal experiment: {len(df)}")
    report.append("")

    best_pf = df.iloc[df["Profit Factor"].idxmax()]
    best_score = df.iloc[df["EdgeCraft Score"].idxmax()]
    lowest_dd = df.iloc[df["Max Drawdown"].idxmin()]

    baseline = df.iloc[0]

    report.append("EXECUTIVE SUMMARY")
    report.append("----------------------------")
    report.append(_generate_summary(best_score, baseline))
    report.append("")

    report.append("BASELINE")
    report.append("----------------------------")
    report.append(_format_result(baseline))
    report.append("")

    report.append("BÄSTA EDGECRAFT SCORE")
    report.append("----------------------------")
    report.append(_format_result(best_score))
    report.append("")

    report.append("BÄSTA PROFIT FACTOR")
    report.append("----------------------------")
    report.append(_format_result(best_pf))
    report.append("")

    report.append("LÄGSTA DRAWDOWN")
    report.append("----------------------------")
    report.append(_format_result(lowest_dd))
    report.append("")

    report.append("FÖRBÄTTRING MOT BASELINE")
    report.append("----------------------------")
    report.append(_compare_to_baseline(best_score, baseline))
    report.append("")

    report.append("AI-BEDÖMNING")
    report.append("----------------------------")
    report.append(_ai_judgement(best_score, baseline, df))
    report.append("")

    report.append("=" * 60)

    return "\n".join(report)


def _format_result(row):
    lines = []

    fields = [
        "Market",
        "Timeframe",
        "Exit Days",
        "Trend Filter",
        "Total Return",
        "CAGR",
        "Max Drawdown",
        "Win Rate",
        "Winrate",
        "Profit Factor",
        "Trades",
        "EdgeCraft Score",
    ]

    for field in fields:
        if field in row.index:
            lines.append(f"{field}: {row[field]}")

    return "\n".join(lines)


def _compare_to_baseline(best, baseline):
    lines = []

    comparisons = [
        "Total Return",
        "CAGR",
        "Profit Factor",
        "Win Rate",
        "Winrate",
        "Max Drawdown",
        "EdgeCraft Score",
        "Trades",
    ]

    for col in comparisons:
        if col in best.index and col in baseline.index:
            try:
                best_value = float(best[col])
                base_value = float(baseline[col])
                diff = best_value - base_value

                if base_value != 0:
                    pct = (diff / abs(base_value)) * 100
                    lines.append(
                        f"{col}: {base_value:.2f} → {best_value:.2f} "
                        f"({diff:+.2f}, {pct:+.1f}%)"
                    )
                else:
                    lines.append(
                        f"{col}: {base_value:.2f} → {best_value:.2f} "
                        f"({diff:+.2f})"
                    )

            except Exception:
                lines.append(f"{col}: {baseline[col]} → {best[col]}")

    return "\n".join(lines)


def _generate_summary(best, baseline):
    try:
        best_score = float(best["EdgeCraft Score"])
        base_score = float(baseline["EdgeCraft Score"])
        best_pf = float(best["Profit Factor"])
        trades = int(best["Trades"])
    except Exception:
        return "Rapporten kunde inte skapa en fullständig sammanfattning."

    if best_score > base_score and best_pf > 1.2 and trades >= 30:
        return (
            "Strategin visar förbättring mot baseline och har tecken på edge. "
            "Resultatet behöver verifieras med Walk Forward och Monte Carlo."
        )

    if best_pf > 1.0 and trades >= 30:
        return (
            "Strategin visar viss positiv edge, men resultatet är ännu inte starkt nog "
            "för att betraktas som robust."
        )

    return (
        "Strategin visar ännu ingen tydlig statistisk edge. "
        "Mer testning krävs innan slutsats kan dras."
    )


def _ai_judgement(best, baseline, df):
    lines = []

    try:
        best_pf = float(best["Profit Factor"])
        best_score = float(best["EdgeCraft Score"])
        base_score = float(baseline["EdgeCraft Score"])
        trades = int(best["Trades"])
    except Exception:
        return "AI-bedömning kunde inte göras eftersom viktiga värden saknas."

    if best_score > base_score:
        lines.append("Bästa varianten slår baseline enligt EdgeCraft Score.")
    else:
        lines.append("Baseline är fortfarande lika stark eller starkare än bästa varianten.")

    if best_pf >= 1.5:
        lines.append("Profit Factor är stark.")
    elif best_pf >= 1.2:
        lines.append("Profit Factor är positiv men behöver verifieras.")
    elif best_pf > 1.0:
        lines.append("Profit Factor är svagt positiv.")
    else:
        lines.append("Profit Factor visar ingen tydlig edge.")

    if trades >= 100:
        lines.append("Antalet trades är bra.")
    elif trades >= 30:
        lines.append("Antalet trades är acceptabelt men inte optimalt.")
    else:
        lines.append("Antalet trades är för lågt för säker slutsats.")

    profitable_count = len(df[df["Profit Factor"] > 1.0])
    profitable_ratio = profitable_count / len(df)

    if profitable_ratio >= 0.7:
        lines.append("Många kombinationer är lönsamma, vilket stärker robustheten.")
    elif profitable_ratio >= 0.4:
        lines.append("Vissa kombinationer är lönsamma, men robustheten är medel.")
    else:
        lines.append("Få kombinationer är lönsamma, vilket gör edgen osäker.")

    lines.append("")
    lines.append("Nästa steg: Walk Forward-test.")

    return "\n".join(lines)
