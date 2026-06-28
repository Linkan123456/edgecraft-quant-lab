from engine.qualification_engine import run_qualification_engine
from engine.improvement_advisor import generate_improvement_advice


def generate_executive_summary(
    best,
    strategy_dna,
    robustness_report,
    walk_forward_report,
    monte_carlo_report,
    algo_report,
):
    qualification = run_qualification_engine(
        best=best,
        strategy_dna=strategy_dna,
        robustness_report=robustness_report,
        walk_forward_report=walk_forward_report,
        monte_carlo_report=monte_carlo_report,
        algo_report=algo_report,
    )

    score = qualification["score"]
    status = qualification["status"]

    if status == "READY_FOR_LIVE_TEST":
        stars = "★★★★★"

    elif status == "STRONG_CANDIDATE":
        stars = "★★★★☆"

    elif status == "NEEDS_MORE_TESTING":
        stars = "★★★☆☆"

    else:
        stars = "★☆☆☆☆"

    advice = generate_improvement_advice(best)

    return {
        "stars": stars,
        "status": status,
        "score": score,
        "recommendation": qualification["recommendation"],
        "best_market": strategy_dna.get("best_market"),
        "best_timeframe": strategy_dna.get("best_timeframe"),
        "best_trading_style": strategy_dna.get("best_trading_style"),
        "avoid_markets": strategy_dna.get("avoid_markets", []),
        "reasons": qualification["reasons"],
        "improvement_advice": advice,
    }