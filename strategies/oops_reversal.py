import pandas as pd

from strategies.base import BaseStrategy


def add_oops_reversal_signals(
    data: pd.DataFrame,
    exit_days: int = 1,
    trend_filter: str = "None"
) -> pd.DataFrame:
    df = data.copy()

    df["PrevLow"] = df["Low"].shift(1)

    if trend_filter == "EMA100":
        df["TrendMA"] = df["Close"].ewm(span=100, adjust=False).mean()
        trend_ok = df["Close"] > df["TrendMA"]

    elif trend_filter == "EMA200":
        df["TrendMA"] = df["Close"].ewm(span=200, adjust=False).mean()
        trend_ok = df["Close"] > df["TrendMA"]

    else:
        trend_ok = True

    df["BuySignal"] = (
        (df["Open"] < df["PrevLow"]) &
        (df["Close"] > df["PrevLow"]) &
        trend_ok
    )

    df["SellSignal"] = False

    for i in range(len(df)):
        if df["BuySignal"].iloc[i]:
            exit_index = i + exit_days

            if exit_index < len(df):
                df.iloc[
                    exit_index,
                    df.columns.get_loc("SellSignal")
                ] = True

    return df


class OOPSReversalStrategy(BaseStrategy):
    name = "OOPS Reversal"
    version = "0.3"
    description = "OOPS close-version med valbart trendfilter."
    asset_classes = ["ETF", "Index", "Stocks"]
    tags = ["Reversal", "Gap", "Mean Reversion", "Long Only"]

    def generate_signals(self, data, **parameters):
        return add_oops_reversal_signals(
            data=data,
            exit_days=parameters.get("exit_days", 1),
            trend_filter=parameters.get("trend_filter", "None")
        )

    def default_parameters(self):
        return {
            "exit_days": 3,
            "trend_filter": "None"
        }

    def parameter_grid(self):
        return {
            "exit_days": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 15, 20],
            "trend_filter": ["None", "EMA100", "EMA200"]
        }

    def supports_intraday(self):
        return False

    def supports_weekly(self):
        return False