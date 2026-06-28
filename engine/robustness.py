import pandas as pd


RESULT_COLUMNS = {
    "Profit Factor",
    "Winrate",
    "Max Drawdown",
    "Trades",
    "Total Return",
    "Avg Trade",
    "EdgeCraft Score",
    "Approved",
    "Robustness Pass",
    "Algo Readiness",
    "Recommendation",
}


IDENTITY_COLUMNS = {
    "Strategy",
    "Strategy Name",
    "Market",
    "Symbol",
    "Timeframe",
}


def run_robustness_analysis(
    research_df: pd.DataFrame,
    score_column: str = "EdgeCraft Score",
    min_score_ratio: float = 0.80,
    parameter_columns: list | None = None,
):
    if research_df is None or research_df.empty:
        return pd.DataFrame(), {
            "status": "NO_DATA",
            "message": "Ingen data fanns att analysera i Robustness.",
            "is_robust": False,
            "best_score": None,
            "robust_rows": 0,
            "total_rows": 0,
            "robust_ratio": 0,
            "parameter_stability": [],
        }

    df = research_df.copy()

    if score_column not in df.columns:
        return df, {
            "status": "MISSING_SCORE_COLUMN",
            "message": f"Kolumnen '{score_column}' saknas.",
            "is_robust": False,
            "best_score": None,
            "robust_rows": 0,
            "total_rows": len(df),
            "robust_ratio": 0,
            "parameter_stability": [],
        }

    df[score_column] = pd.to_numeric(df[score_column], errors="coerce")
    df = df.dropna(subset=[score_column])

    if df.empty:
        return df, {
            "status": "NO_VALID_SCORE",
            "message": "Inga giltiga score-värden fanns för Robustness.",
            "is_robust": False,
            "best_score": None,
            "robust_rows": 0,
            "total_rows": 0,
            "robust_ratio": 0,
            "parameter_stability": [],
        }

    best_score = df[score_column].max()
    min_allowed_score = best_score * min_score_ratio

    df["Robustness Pass"] = df[score_column] >= min_allowed_score
    robustness_df = df[df["Robustness Pass"]].copy()

    if parameter_columns is None:
        parameter_columns = detect_parameter_columns(df)

    report = generate_robustness_report(
        research_df=df,
        robustness_df=robustness_df,
        score_column=score_column,
        min_score_ratio=min_score_ratio,
        best_score=best_score,
        parameter_columns=parameter_columns,
    )

    return robustness_df, report


def detect_parameter_columns(df: pd.DataFrame) -> list:
    parameter_columns = []

    blocked_columns = RESULT_COLUMNS.union(IDENTITY_COLUMNS)

    for col in df.columns:
        if col in blocked_columns:
            continue

        if col.startswith("Unnamed"):
            continue

        unique_count = df[col].nunique(dropna=True)

        if unique_count <= 1:
            continue

        if unique_count > 30:
            continue

        parameter_columns.append(col)

    return parameter_columns


def generate_robustness_report(
    research_df: pd.DataFrame,
    robustness_df: pd.DataFrame,
    score_column: str,
    min_score_ratio: float,
    best_score: float,
    parameter_columns: list | None = None,
):
    total_rows = len(research_df)
    robust_rows = len(robustness_df)
    robust_ratio = robust_rows / total_rows if total_rows else 0

    report = {
        "status": "OK",
        "message": "Robustness-analysen kördes klart.",
        "is_robust": robust_ratio >= 0.20,
        "best_score": round(float(best_score), 4) if pd.notna(best_score) else None,
        "min_score_ratio": min_score_ratio,
        "total_rows": total_rows,
        "robust_rows": robust_rows,
        "robust_ratio": round(float(robust_ratio), 4),
        "parameter_columns_used": parameter_columns or [],
        "parameter_stability": [],
        "market_stability": [],
        "timeframe_stability": [],
    }

    if parameter_columns is None:
        parameter_columns = []

    for param in parameter_columns:
        stability = analyze_column_stability(
            df=research_df,
            column=param,
            score_column=score_column,
        )

        if stability is not None:
            report["parameter_stability"].append(stability)

    if "Market" in research_df.columns:
        market_stability = analyze_column_stability(
            df=research_df,
            column="Market",
            score_column=score_column,
        )
        if market_stability is not None:
            report["market_stability"].append(market_stability)

    if "Timeframe" in research_df.columns:
        timeframe_stability = analyze_column_stability(
            df=research_df,
            column="Timeframe",
            score_column=score_column,
        )
        if timeframe_stability is not None:
            report["timeframe_stability"].append(timeframe_stability)

    return report


def analyze_column_stability(
    df: pd.DataFrame,
    column: str,
    score_column: str,
):
    if column not in df.columns or score_column not in df.columns:
        return None

    temp_df = df.dropna(subset=[column, score_column]).copy()

    if temp_df.empty:
        return None

    grouped = (
        temp_df
        .groupby(column, as_index=False)
        .agg(
            Avg_Score=(score_column, "mean"),
            Count=(score_column, "count"),
            Max_Score=(score_column, "max"),
        )
        .sort_values("Avg_Score", ascending=False)
        .reset_index(drop=True)
    )

    if grouped.empty:
        return None

    best_row = grouped.iloc[0]

    return {
        "column": column,
        "best_value": clean_value(best_row[column]),
        "avg_score": round(float(best_row["Avg_Score"]), 4),
        "max_score": round(float(best_row["Max_Score"]), 4),
        "count": int(best_row["Count"]),
        "tested_values": int(len(grouped)),
    }


def clean_value(value):
    try:
        if pd.isna(value):
            return None
    except Exception:
        pass

    if hasattr(value, "item"):
        return value.item()

    return value