# engine/research_pipeline.py
# EdgeCraft Quant Lab - Research Pipeline v0.11

import pandas as pd


STABILITY_VARIANT_COLUMNS = [
    "require_new_higher_high",
]


SORT_COLUMNS_PRIORITY = [
    "EdgeCraft Score",
    "Profit Factor",
    "Total Return",
]


def _existing_columns(df: pd.DataFrame, columns):
    return [column for column in columns if column in df.columns]


def _sort_research_df(df: pd.DataFrame) -> pd.DataFrame:
    sort_columns = _existing_columns(df, SORT_COLUMNS_PRIORITY)

    if not sort_columns:
        return df.reset_index(drop=True)

    return df.sort_values(
        by=sort_columns,
        ascending=False,
    ).reset_index(drop=True)


def _candidate_identity_columns(df: pd.DataFrame, variant_columns):
    """
    Gruppnyckel för att hitta samma kandidat med olika stabilitetsfilter.
    Vi jämför t.ex. AMD 1d 3R ATR 1.0 exit 10 HH=False mot HH=True.
    """

    preferred = [
        "Strategy",
        "Market",
        "Timeframe",
        "Exit Model",
        "stop_type",
        "atr_multiple",
        "exit_days",
        "entry_trigger",
        "volume_filter",
        "pullback_min_days",
        "pullback_max_days",
        "near_high_pct",
    ]

    excluded = set(variant_columns)
    excluded.update([
        "EdgeCraft Score",
        "Profit Factor",
        "Winrate",
        "Max Drawdown",
        "Trades",
        "Total Return",
        "Avg Trade",
        "Approved",
        "Error",
    ])

    identity = [column for column in preferred if column in df.columns and column not in excluded]

    if identity:
        return identity

    return [
        column for column in df.columns
        if column not in excluded
    ]


def _add_stability_variants(
    sorted_df: pd.DataFrame,
    selected_df: pd.DataFrame,
    top_n: int,
    score_tolerance: float = 0.15,
) -> pd.DataFrame:
    """
    Låter viktiga stabilitetsvarianter följa med till Exit Research.

    Exempel:
    Om HH=False är bäst men HH=True ligger inom 15 % av samma kandidat,
    får även HH=True följa med trots att den inte ligger i absolut topp-score.
    """

    variant_columns = _existing_columns(sorted_df, STABILITY_VARIANT_COLUMNS)

    if sorted_df.empty or selected_df.empty or not variant_columns:
        return selected_df

    identity_columns = _candidate_identity_columns(sorted_df, variant_columns)

    if not identity_columns or "EdgeCraft Score" not in sorted_df.columns:
        return selected_df

    selected_indices = set(selected_df.index.tolist())
    extra_indices = []

    # Undvik att topp 5 bara blir samma symbol/parameter utan stabilitetsjämförelse.
    max_candidates = max(top_n, min(len(sorted_df), top_n * 2))

    for _, selected_row in selected_df.iterrows():
        group_mask = pd.Series(True, index=sorted_df.index)

        for column in identity_columns:
            group_mask = group_mask & (sorted_df[column] == selected_row.get(column))

        group = sorted_df[group_mask].copy()

        if group.empty:
            continue

        best_score = float(group["EdgeCraft Score"].max() or 0)

        if best_score <= 0:
            continue

        min_allowed_score = best_score * (1 - score_tolerance)
        group = group[group["EdgeCraft Score"] >= min_allowed_score].copy()

        for variant_column in variant_columns:
            variant_values = selected_df[variant_column].dropna().unique().tolist()
            alternatives = group[~group[variant_column].isin(variant_values)].copy()
            alternatives = _sort_research_df(alternatives)

            for index in alternatives.index.tolist():
                if index not in selected_indices and index not in extra_indices:
                    extra_indices.append(index)
                    break

        if len(selected_indices) + len(extra_indices) >= max_candidates:
            break

    if not extra_indices:
        return selected_df

    combined = pd.concat(
        [
            selected_df,
            sorted_df.loc[extra_indices],
        ],
        ignore_index=False,
    )

    combined = combined[~combined.index.duplicated(keep="first")]
    combined = _sort_research_df(combined)

    return combined.head(max_candidates)


def get_top_candidates(
    research_df: pd.DataFrame,
    top_n: int = 5,
    min_trades: int = 20,
) -> pd.DataFrame:
    """
    Tar fram de bästa kandidaterna efter snabb screening.
    Används innan tunga tester som Exit Research, Walk Forward och Monte Carlo.

    Viktigt:
    Vi väljer inte längre enbart absolut topp-score.
    Viktiga stabilitetsvarianter, t.ex. require_new_higher_high=True/False,
    får följa med om de ligger nära bästa kandidat.
    """

    if research_df is None or research_df.empty:
        return pd.DataFrame()

    df = research_df.copy()

    if "Trades" in df.columns:
        df = df[df["Trades"] >= min_trades].copy()

    if df.empty:
        return pd.DataFrame()

    df = _sort_research_df(df)

    selected = df.head(top_n).copy()
    selected = _add_stability_variants(
        sorted_df=df,
        selected_df=selected,
        top_n=top_n,
        score_tolerance=0.15,
    )

    return selected.reset_index(drop=True)


def get_best_candidate(
    research_df: pd.DataFrame,
    min_trades: int = 20,
):
    """
    Returnerar bästa kandidat efter screening.
    """

    top = get_top_candidates(
        research_df=research_df,
        top_n=1,
        min_trades=min_trades,
    )

    if top is None or top.empty:
        return None

    return top.iloc[0]


def generate_research_summary(
    research_df: pd.DataFrame,
    top_df: pd.DataFrame,
) -> str:
    """
    Skapar en kort forskningsrapport.
    """

    lines = []
    lines.append("=" * 60)
    lines.append("EDGECRAFT RESEARCH PIPELINE v0.11")
    lines.append("=" * 60)
    lines.append("")

    total_tests = 0 if research_df is None else len(research_df)
    top_count = 0 if top_df is None else len(top_df)

    lines.append(f"Totalt antal screening-tester: {total_tests}")
    lines.append(f"Kandidater som går vidare: {top_count}")
    lines.append("")

    if top_df is None or top_df.empty:
        lines.append("Inga kandidater klarade första screening.")
        lines.append("=" * 60)
        return "\n".join(lines)

    lines.append("TOPPKANDIDATER")
    lines.append("----------------------------")

    for _, row in top_df.iterrows():
        market = row.get("Market", "N/A")
        timeframe = row.get("Timeframe", "N/A")
        score = row.get("EdgeCraft Score", "N/A")
        pf = row.get("Profit Factor", "N/A")
        trades = row.get("Trades", "N/A")
        hh_filter = row.get("require_new_higher_high", "N/A")

        lines.append(
            f"{market} | {timeframe} | "
            f"Score {score} | PF {pf} | Trades {trades} | HH {hh_filter}"
        )

    lines.append("")
    lines.append("Nästa steg:")
    lines.append("Kör tyngre tester endast på toppkandidaterna, men behåll viktiga stabilitetsvarianter för jämförelse.")
    lines.append("=" * 60)

    return "\n".join(lines)
