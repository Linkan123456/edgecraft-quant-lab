import pandas as pd

from engine.auto_improvement_engine import run_auto_improvement


def run_improvement_pipeline(
    research_df,
    parameter_grid=None,
):
    """
    Kör första versionen av Auto Improvement Engine.

    Den gör ännu inga nya backtester.
    Den bygger endast upp nästa parameteruppsättning
    som sedan ska skickas vidare till Optimizer.
    """

    if research_df is None or research_df.empty:
        return {
            "results": pd.DataFrame(),
            "parameter_grid": parameter_grid or {},
            "parameter_sets": [],
            "total_tests": 0,
            "report": "Ingen data att förbättra."
        }

    improvement = run_auto_improvement(
        results_df=research_df,
        existing_parameter_grid=parameter_grid,
    )

    report = (
        "=========================================\n"
        "EDGECRAFT AUTO IMPROVEMENT ENGINE v0.10\n"
        "=========================================\n\n"
        f"Nya parameterkombinationer: {improvement['total_tests']}\n"
        f"Totalt antal kandidater: {len(improvement['results'])}\n\n"
        "Testade parametrar\n"
        "-----------------\n"
    )

    for key, values in improvement["parameter_grid"].items():
        report += f"{key}: {values}\n"

    report += (
        "\n"
        "STATUS\n"
        "-----------------\n"
        "Auto Improvement har byggt nya parameterkombinationer.\n"
        "Nästa steg är att köra fullständiga backtester på samtliga kombinationer.\n"
    )

    return {
        "results": improvement["results"],
        "parameter_grid": improvement["parameter_grid"],
        "parameter_sets": improvement["parameter_sets"],
        "total_tests": improvement["total_tests"],
        "report": report,
    }