import pandas as pd

from strategies.base import BaseStrategy


def add_double_seven_signals(
    data: pd.DataFrame,
    ma_length: int,
    entry_lookback: int,
    exit_lookback: int
) -> pd.DataFrame:
    df = data.copy()

    df["MA"] = df["Close"].rolling(ma_length).mean()
    df["LowestClose"] = df["Close"].rolling(entry_lookback).min()
    df["HighestClose"] = df["Close"].rolling(exit_lookback).max()

    df["BuySignal"] = (
        (df["Close"] > df["MA"]) &
        (df["Close"] == df["LowestClose"])
    )

    df["SellSignal"] = (
        df["Close"] == df["HighestClose"]
    )

    return df


class DoubleSevenStrategy(BaseStrategy):
    name = "Double Seven"
    version = "1.0"
    description = "Mean reversion-strategi som köper lägsta stängning i upptrend och säljer högsta stängning."
    asset_classes = ["ETF", "Index", "Stocks"]
    tags = ["Mean Reversion", "Long Only", "Daily"]

    def generate_signals(self, data, **parameters):
        return add_double_seven_signals(
            data=data,
            ma_length=parameters.get("ma_length", 200),
            entry_lookback=parameters.get("entry_lookback", 7),
            exit_lookback=parameters.get("exit_lookback", 7)
        )

    def default_parameters(self):
        return {
            "ma_length": 200,
            "entry_lookback": 7,
            "exit_lookback": 7
        }

    def parameter_grid(self):
        return {
            "ma_length": [50, 100, 150, 200, 250, 300],
            "entry_lookback": [3, 5, 7, 10, 14, 20],
            "exit_lookback": [3, 5, 7, 10, 14, 20]
        }