import pandas as pd
import numpy as np


def run_walk_forward_test(*args, **kwargs):
    data = kwargs.get("data", None)
    trades_df = kwargs.get("trades_df", None)

    if trades_df is None:
        trades_df = data

    wf_df, _ = run_walk_forward_analysis(trades_df=trades_df)
    return wf_df


def generate_walk_forward_summary(walk_forward_df):
    if walk_forward_df is None or walk_forward_df.empty:
        return build_walk_forward_report(
            total_windows=0,
            valid_windows=0,
            pass_rate=0,
            profitable_rate=0,
            positive_pf_rate=0,
            avg_pf=0,
            avg_return=0,
            avg_drawdown=0,
            avg_trades=0,
            stability_index=0,
            walk_forward_score=0,
            traffic_light="RÖD - Ingen data",
            assessment="Ingen Walk Forward-data fanns att sammanfatta."
        )

    df = walk_forward_df.copy()

    valid_df = df[
        (df["Trades"] >= 10)
        & (df["Test PF"].notna())
    ].copy()

    total_windows = len(df)
    valid_windows = len(valid_df)

    if valid_windows == 0:
        return build_walk_forward_report(
            total_windows=total_windows,
            valid_windows=0,
            pass_rate=0,
            profitable_rate=0,
            positive_pf_rate=0,
            avg_pf=0,
            avg_return=0,
            avg_drawdown=0,
            avg_trades=0,
            stability_index=0,
            walk_forward_score=0,
            traffic_light="RÖD - För svagt underlag",
            assessment="Inga Walk Forward-fönster hade tillräckligt många trades."
        )

    pass_rate = valid_df["Pass"].mean() * 100
    profitable_rate = (valid_df["Test Return"] > 0).mean() * 100
    positive_pf_rate = (valid_df["Test PF"] > 1.0).mean() * 100

    avg_pf = valid_df["Test PF"].clip(upper=10).mean()
    avg_return = valid_df["Test Return"].mean()
    avg_drawdown = valid_df["Test Drawdown"].mean()
    avg_trades = valid_df["Trades"].mean()

    stability_index = calculate_stability_index(valid_df)

    walk_forward_score = calculate_walk_forward_score(
        valid_windows=valid_windows,
        min_valid_windows=5,
        pass_rate=pass_rate,
        profitable_rate=profitable_rate,
        positive_pf_rate=positive_pf_rate,
        avg_pf=avg_pf,
        avg_drawdown=avg_drawdown,
        stability_index=stability_index,
    )

    traffic_light, assessment = classify_walk_forward_result(
        valid_windows=valid_windows,
        min_valid_windows=5,
        avg_trades=avg_trades,
        pass_rate=pass_rate,
        walk_forward_score=walk_forward_score,
    )

    return build_walk_forward_report(
        total_windows=total_windows,
        valid_windows=valid_windows,
        pass_rate=pass_rate,
        profitable_rate=profitable_rate,
        positive_pf_rate=positive_pf_rate,
        avg_pf=avg_pf,
        avg_return=avg_return,
        avg_drawdown=avg_drawdown,
        avg_trades=avg_trades,
        stability_index=stability_index,
        walk_forward_score=walk_forward_score,
        traffic_light=traffic_light,
        assessment=assessment,
    )


def run_walk_forward_analysis(
    trades_df=None,
    initial_capital=100000,
    min_trades_per_window=10,
    min_valid_windows=5,
):
    if trades_df is None or trades_df.empty:
        return pd.DataFrame(), ""

    df = trades_df.copy()

    if "Return" not in df.columns:
        if "PnL" in df.columns:
            df["Return"] = df["PnL"]
        elif "Profit" in df.columns:
            df["Return"] = df["Profit"]
        else:
            return pd.DataFrame(), ""

    df["Return"] = pd.to_numeric(df["Return"], errors="coerce")
    df = df.dropna(subset=["Return"]).reset_index(drop=True)

    if df.empty:
        return pd.DataFrame(), ""

    total_trades = len(df)

    window_size = max(min_trades_per_window, total_trades // 10)
    step_size = max(1, window_size // 2)

    results = []

    for start in range(0, total_trades - window_size + 1, step_size):
        window = df.iloc[start:start + window_size].copy()

        trades = len(window)
        total_return = window["Return"].sum()

        gross_profit = window.loc[window["Return"] > 0, "Return"].sum()
        gross_loss = abs(window.loc[window["Return"] < 0, "Return"].sum())

        if gross_loss == 0:
            profit_factor = np.nan
        else:
            profit_factor = gross_profit / gross_loss

        equity_curve = initial_capital + window["Return"].cumsum()
        running_max = equity_curve.cummax()
        drawdown = (equity_curve - running_max) / running_max * 100
        max_drawdown = abs(drawdown.min()) if not drawdown.empty else 0

        passed = (
            trades >= min_trades_per_window
            and total_return > 0
            and pd.notna(profit_factor)
            and profit_factor > 1.0
            and max_drawdown <= 25
        )

        results.append({
            "Window": len(results) + 1,
            "Start Trade": start + 1,
            "End Trade": start + window_size,
            "Trades": trades,
            "Test PF": round(float(profit_factor), 3) if pd.notna(profit_factor) else None,
            "Test Return": round(float(total_return), 2),
            "Test Drawdown": round(float(max_drawdown), 2),
            "Pass": passed,
        })

    wf_df = pd.DataFrame(results)
    wf_report = generate_walk_forward_summary(wf_df)

    return wf_df, wf_report


def calculate_stability_index(valid_df):
    if valid_df is None or valid_df.empty:
        return 0

    returns = valid_df["Test Return"].astype(float)

    if len(returns) < 2:
        return 0

    avg_return = returns.mean()
    std_return = returns.std()

    if std_return == 0:
        return 100

    raw_score = avg_return / std_return * 25
    return round(float(max(0, min(100, raw_score))), 2)


def calculate_walk_forward_score(
    valid_windows,
    min_valid_windows,
    pass_rate,
    profitable_rate,
    positive_pf_rate,
    avg_pf,
    avg_drawdown,
    stability_index,
):
    data_score = min(100, (valid_windows / min_valid_windows) * 100)
    pf_score = min(100, max(0, (avg_pf - 1.0) * 50))
    dd_score = max(0, 100 - avg_drawdown * 3)

    score = (
        data_score * 0.20
        + pass_rate * 0.25
        + profitable_rate * 0.15
        + positive_pf_rate * 0.15
        + pf_score * 0.10
        + dd_score * 0.10
        + stability_index * 0.05
    )

    return round(float(max(0, min(100, score))), 2)


def classify_walk_forward_result(
    valid_windows,
    min_valid_windows,
    avg_trades,
    pass_rate,
    walk_forward_score,
):
    if valid_windows < min_valid_windows:
        return (
            "GUL - För lite data",
            "Walk Forward-resultatet är inte tillräckligt verifierat. För få godkända testfönster gör att strategin kräver mer data."
        )

    if avg_trades < 10:
        return (
            "GUL - För få trades per fönster",
            "Walk Forward-resultatet bygger på för få trades per testfönster."
        )

    if walk_forward_score >= 75 and pass_rate >= 70:
        return (
            "GRÖN - Robust",
            "Strategin visar stark Walk Forward-robusthet över flera testfönster."
        )

    if walk_forward_score >= 50:
        return (
            "GUL - Lovande men kräver mer test",
            "Strategin visar potential, men Walk Forward-resultatet är inte tillräckligt starkt för att ensam bekräfta algo-kvalitet."
        )

    return (
        "RÖD - Ej robust",
        "Strategin klarar inte Walk Forward-testet tillräckligt bra."
    )


def build_walk_forward_report(
    total_windows,
    valid_windows,
    pass_rate,
    profitable_rate,
    positive_pf_rate,
    avg_pf,
    avg_return,
    avg_drawdown,
    avg_trades,
    stability_index,
    walk_forward_score,
    traffic_light,
    assessment,
):
    return f"""
============================================================
EDGECRAFT WALK FORWARD REPORT v0.76
============================================================

Antal testfönster totalt: {total_windows}
Godkända testfönster med tillräckligt antal trades: {valid_windows}

Minimikrav:
- Minst 5 godkända testfönster
- Minst 10 trades per fönster
- PF över 1.0
- Positiv avkastning
- Rimlig drawdown

Andel godkända fönster med PF > 1.0: {positive_pf_rate:.2f}%
Andel godkända fönster med positiv avkastning: {profitable_rate:.2f}%
Andel fönster som klarar Pass/Fail: {pass_rate:.2f}%

Genomsnittlig Test PF: {avg_pf:.3f}
Genomsnittlig Test Return: {avg_return:.2f}
Genomsnittlig Test Drawdown: {avg_drawdown:.2f}%
Genomsnittligt antal trades: {avg_trades:.1f}

Stability Index: {stability_index}
Walk Forward Score: {walk_forward_score}
Trafikljus: {traffic_light}

BEDÖMNING
----------------------------
{assessment}

VIKTIGT
----------------------------
Walk Forward får inte bli grönt om underlaget är för tunt.
Ett extremt högt PF-värde räcker inte om det bygger på för få trades.

============================================================
"""


def generate_walk_forward_report(*args, **kwargs):
    return build_walk_forward_report(*args, **kwargs)