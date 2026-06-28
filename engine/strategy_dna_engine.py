import pandas as pd


INDEX_MARKETS = {
    "SPY", "QQQ", "DIA", "IWM", "DAX", "NDX", "SPX", "ES", "NQ"
}

SECTOR_ETF_MARKETS = {
    "XLK", "XLF", "XLE", "XLV", "XLY", "XLI", "XLP", "XLU", "XLB", "XLRE", "XLC"
}

FOREX_MARKETS = {
    "EURUSD", "GBPUSD", "USDJPY", "USDCHF", "USDCAD", "AUDUSD", "NZDUSD",
    "EUR/USD", "GBP/USD", "USD/JPY", "USD/CHF", "USD/CAD", "AUD/USD", "NZD/USD"
}

COMMODITY_MARKETS = {
    "GC", "SI", "CL", "NG", "GOLD", "SILVER", "OIL", "WTI", "BRENT"
}

CRYPTO_MARKETS = {
    "BTC", "ETH", "BTCUSD", "ETHUSD", "BTC/USD", "ETH/USD"
}


def safe_float(value, default=0.0):
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def normalize_market(value):
    if value is None:
        return "UNKNOWN"

    return str(value).upper().replace("-", "").replace(" ", "")


def classify_market(market):
    normalized = normalize_market(market)

    if normalized in INDEX_MARKETS:
        return "Index / bred ETF"

    if normalized in SECTOR_ETF_MARKETS:
        return "Sektor-ETF"

    if normalized in FOREX_MARKETS:
        return "Forex"

    if normalized in COMMODITY_MARKETS:
        return "Råvaror"

    if normalized in CRYPTO_MARKETS:
        return "Krypto"

    return "Aktier / övrigt"


def classify_timeframe(timeframe):
    tf = str(timeframe).lower().strip()

    if tf in ["1m", "3m", "5m", "15m", "30m"]:
        return "Intradag"

    if tf in ["1h", "2h", "4h"]:
        return "Kort swing / forex-liknande"

    if tf in ["1d", "d", "daily"]:
        return "Swing"

    if tf in ["1w", "w", "weekly"]:
        return "Position"

    return "Okänd"


def get_score_column(df):
    for column in ["EdgeCraft Score", "Score", "edgecraft_score", "score"]:
        if column in df.columns:
            return column

    return None


def get_market_column(df):
    for column in ["Market", "Symbol", "Ticker", "market", "symbol"]:
        if column in df.columns:
            return column

    return None


def get_timeframe_column(df):
    for column in ["Timeframe", "timeframe"]:
        if column in df.columns:
            return column

    return None


def build_group_summary(df, group_column, score_column):
    if df is None or df.empty or group_column not in df.columns or score_column not in df.columns:
        return []

    grouped = (
        df.groupby(group_column)
        .agg(
            avg_score=(score_column, "mean"),
            max_score=(score_column, "max"),
            count=(score_column, "count"),
        )
        .reset_index()
        .sort_values(["avg_score", "max_score"], ascending=False)
    )

    return grouped.to_dict("records")


def rating_from_score(avg_score, best_score):
    avg_score = safe_float(avg_score)
    best_score = safe_float(best_score)

    if best_score <= 0:
        return "☆☆☆☆☆"

    ratio = avg_score / best_score

    if ratio >= 0.80:
        return "⭐⭐⭐⭐⭐"
    if ratio >= 0.65:
        return "⭐⭐⭐⭐☆"
    if ratio >= 0.50:
        return "⭐⭐⭐☆☆"
    if ratio >= 0.35:
        return "⭐⭐☆☆☆"
    if ratio > 0:
        return "⭐☆☆☆☆"

    return "☆☆☆☆☆"


def build_strategy_dna(all_results_df, best, robustness_ratio, final_decision):
    if all_results_df is None or all_results_df.empty:
        return {
            "status": "NO_DATA",
            "summary": "Strategy DNA kunde inte byggas eftersom testresultat saknas.",
        }

    df = all_results_df.copy()

    score_column = get_score_column(df)
    market_column = get_market_column(df)
    timeframe_column = get_timeframe_column(df)

    if score_column is None:
        return {
            "status": "NO_SCORE",
            "summary": "Strategy DNA kunde inte byggas eftersom score-kolumn saknas.",
        }

    best_score = safe_float(df[score_column].max())

    if market_column:
        df["Asset Class"] = df[market_column].apply(classify_market)
    else:
        df["Asset Class"] = "Okänd"

    if timeframe_column:
        df["Trading Style"] = df[timeframe_column].apply(classify_timeframe)
    else:
        df["Trading Style"] = "Okänd"

    asset_class_summary = build_group_summary(df, "Asset Class", score_column)
    timeframe_summary = build_group_summary(df, timeframe_column, score_column) if timeframe_column else []
    trading_style_summary = build_group_summary(df, "Trading Style", score_column)

    best_asset_class = asset_class_summary[0]["Asset Class"] if asset_class_summary else "Okänd"
    best_trading_style = trading_style_summary[0]["Trading Style"] if trading_style_summary else "Okänd"
    best_timeframe = timeframe_summary[0][timeframe_column] if timeframe_summary and timeframe_column else "Okänd"

    avoid_asset_classes = []
    for row in asset_class_summary:
        if safe_float(row["avg_score"]) < best_score * 0.35:
            avoid_asset_classes.append(row["Asset Class"])

    if final_decision == "ANVÄND":
        recommendation = (
            f"Strategin är främst lämpad för {best_asset_class} på {best_timeframe}. "
            f"Den passar bäst som {best_trading_style.lower()}."
        )
    elif final_decision == "KRÄVER MER TEST":
        recommendation = (
            f"Strategin är intressant men inte färdigcertifierad. Den verkar passa bäst för "
            f"{best_asset_class} på {best_timeframe}, men behöver mer verifiering."
        )
    else:
        recommendation = (
            f"Strategin ska inte användas som färdig tradingstrategi ännu. "
            f"Den visar bäst tendens på {best_asset_class} / {best_timeframe}, "
            f"men robustheten är för svag."
        )

    return {
        "status": "OK",
        "best_asset_class": best_asset_class,
        "best_timeframe": best_timeframe,
        "best_trading_style": best_trading_style,
        "asset_class_summary": asset_class_summary,
        "timeframe_summary": timeframe_summary,
        "trading_style_summary": trading_style_summary,
        "avoid_asset_classes": avoid_asset_classes,
        "robustness_ratio": robustness_ratio,
        "final_decision": final_decision,
        "recommendation": recommendation,
        "best_score": best_score,
        "score_column": score_column,
        "market_column": market_column,
        "timeframe_column": timeframe_column,
    }