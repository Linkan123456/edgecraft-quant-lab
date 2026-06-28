import pandas as pd

from strategies.base import BaseStrategy


def add_professional_pullback_signals(
    data: pd.DataFrame,
    ma_fast: int = 20,
    ma_slow: int = 50,
    ma_long: int = 200,
    pullback_min_days: int = 2,
    pullback_max_days: int = 10,
    near_high_pct: float = 10.0,
    volume_filter: str = "None",
    entry_trigger: str = "BreakPreviousHigh",
    stop_type: str = "UnderEntryCandle",
    atr_period: int = 14,
    atr_multiple: float = 0.5,
    exit_days: int = 20,
    require_new_higher_high: bool = False,
) -> pd.DataFrame:
    df = data.copy()

    df["MA_Fast"] = df["Close"].rolling(ma_fast).mean()
    df["MA_Slow"] = df["Close"].rolling(ma_slow).mean()
    df["MA_Long"] = df["Close"].rolling(ma_long).mean()

    df["High_52W"] = df["High"].rolling(252).max()
    df["Near_52W_High"] = df["Close"] >= df["High_52W"] * (1 - near_high_pct / 100)

    df["PrevHigh"] = df["High"].shift(1)
    df["PrevLow"] = df["Low"].shift(1)

    df["VolumeMA20"] = df["Volume"].rolling(20).mean()

    high_low = df["High"] - df["Low"]
    high_close = (df["High"] - df["Close"].shift(1)).abs()
    low_close = (df["Low"] - df["Close"].shift(1)).abs()
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df["ATR"] = true_range.rolling(atr_period).mean()

    trend_ok = (
        (df["Close"] > df["MA_Fast"]) &
        (df["MA_Fast"] > df["MA_Slow"]) &
        (df["MA_Slow"] > df["MA_Long"])
    )

    pullback_days = pd.Series(0, index=df.index)

    for i in range(1, len(df)):
        if df["Close"].iloc[i] < df["Close"].iloc[i - 1]:
            pullback_days.iloc[i] = pullback_days.iloc[i - 1] + 1
        else:
            pullback_days.iloc[i] = 0

    df["PullbackDays"] = pullback_days

    pullback_ok = (
        (df["PullbackDays"].shift(1) >= pullback_min_days) &
        (df["PullbackDays"].shift(1) <= pullback_max_days)
    )

    if volume_filter == "VolumeBelowMA20":
        volume_ok = df["Volume"].shift(1) < df["VolumeMA20"].shift(1)
    elif volume_filter == "VolumeAboveMA20":
        volume_ok = df["Volume"] > df["VolumeMA20"]
    else:
        volume_ok = True

    if entry_trigger == "BreakPreviousHigh":
        entry_ok = df["Close"] > df["PrevHigh"]
    elif entry_trigger == "CloseAboveMAFast":
        entry_ok = df["Close"] > df["MA_Fast"]
    else:
        entry_ok = df["Close"] > df["PrevHigh"]

    buy_signal = (
        trend_ok &
        df["Near_52W_High"] &
        pullback_ok &
        volume_ok &
        entry_ok
    )

    if require_new_higher_high:
        highest_high = df["High"].cummax().shift(1)
        df["NewHigherHigh"] = df["High"] > highest_high

        armed = False
        hh_buy = []

        for i in range(len(df)):
            if bool(df["NewHigherHigh"].iloc[i]):
                armed = True

            if armed and bool(buy_signal.iloc[i]):
                hh_buy.append(True)
                armed = False
            else:
                hh_buy.append(False)

        df["BuySignal"] = hh_buy
    else:
        df["BuySignal"] = buy_signal

    df["SellSignal"] = False

    for i in range(len(df)):
        if df["BuySignal"].iloc[i]:
            exit_index = i + exit_days

            if exit_index < len(df):
                df.iloc[
                    exit_index,
                    df.columns.get_loc("SellSignal")
                ] = True

    if stop_type == "UnderEntryCandle":
        df["StopPrice"] = df["Low"]
    elif stop_type == "UnderPreviousCandle":
        df["StopPrice"] = df["PrevLow"]
    elif stop_type == "ATR":
        df["StopPrice"] = df["Close"] - (df["ATR"] * atr_multiple)
    else:
        df["StopPrice"] = df["Low"]

    return df


class ProfessionalPullbackStrategy(BaseStrategy):
    name = "Professional Pullback"
    version = "1.0"
    description = "Professionell swing-pullback inspirerad av Minervini/Qullamaggie: stark trend, nära 52W high, kontrollerad pullback och breakout-entry."
    asset_classes = ["Stocks", "ETF"]
    tags = ["Swing", "Pullback", "Momentum", "Trend Following", "Long Only"]

    def generate_signals(self, data, **parameters):
        return add_professional_pullback_signals(
            data=data,
            ma_fast=parameters.get("ma_fast", 20),
            ma_slow=parameters.get("ma_slow", 50),
            ma_long=parameters.get("ma_long", 200),
            pullback_min_days=parameters.get("pullback_min_days", 2),
            pullback_max_days=parameters.get("pullback_max_days", 10),
            near_high_pct=parameters.get("near_high_pct", 10.0),
            volume_filter=parameters.get("volume_filter", "None"),
            entry_trigger=parameters.get("entry_trigger", "BreakPreviousHigh"),
            stop_type=parameters.get("stop_type", "UnderEntryCandle"),
            atr_period=parameters.get("atr_period", 14),
            atr_multiple=parameters.get("atr_multiple", 0.5),
            exit_days=parameters.get("exit_days", 20),
            require_new_higher_high=parameters.get("require_new_higher_high", False),
        )

    def default_parameters(self):
        return {
            "ma_fast": 20,
            "ma_slow": 50,
            "ma_long": 200,
            "pullback_min_days": 2,
            "pullback_max_days": 10,
            "near_high_pct": 10.0,
            "volume_filter": "None",
            "entry_trigger": "BreakPreviousHigh",
            "stop_type": "UnderEntryCandle",
            "atr_period": 14,
            "atr_multiple": 0.5,
            "exit_days": 20,
            "require_new_higher_high": False,
        }

    def parameter_grid(self):
        return {
            "ma_fast": [20],
            "ma_slow": [50],
            "ma_long": [200],

            "pullback_min_days": [2],
            "pullback_max_days": [10],

            "near_high_pct": [10],

            "volume_filter": ["None"],

            "entry_trigger": ["BreakPreviousHigh"],

            "stop_type": [
                "UnderEntryCandle",
                "ATR",
            ],

            "atr_multiple": [
                0.5,
                1.0,
            ],

            "exit_days": [
                10,
                20,
            ],

            "require_new_higher_high": [
                False,
                True,
            ],
        }

    def supports_intraday(self):
        return True

    def supports_daily(self):
        return True

    def supports_weekly(self):
        return True

    def supports_long(self):
        return True

    def supports_short(self):
        return False