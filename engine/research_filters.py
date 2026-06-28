# engine/research_filters.py
# EdgeCraft Quant Lab v2 - Professional Filter Library

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List, Optional

import pandas as pd


@dataclass(frozen=True)
class ResearchFilter:
    id: str
    name: str
    description: str
    category: str
    apply: Callable[[pd.DataFrame, Optional[pd.DataFrame]], pd.Series]


def _bool_series(df: pd.DataFrame, value: bool = True) -> pd.Series:
    return pd.Series(value, index=df.index)


def _sma(series: pd.Series, length: int) -> pd.Series:
    return series.rolling(length).mean()


def _ema(series: pd.Series, length: int) -> pd.Series:
    return series.ewm(span=length, adjust=False).mean()


def _atr(df: pd.DataFrame, length: int = 14) -> pd.Series:
    high_low = df["High"] - df["Low"]
    high_close = (df["High"] - df["Close"].shift(1)).abs()
    low_close = (df["Low"] - df["Close"].shift(1)).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return tr.rolling(length).mean()


def _aligned_market_close(df: pd.DataFrame, market_df: Optional[pd.DataFrame]) -> pd.Series:
    if market_df is None or market_df.empty or "Close" not in market_df.columns:
        return pd.Series(index=df.index, dtype=float)
    return market_df["Close"].reindex(df.index).ffill()


def professional_filter_library() -> List[ResearchFilter]:
    return [
        ResearchFilter(
            id="NO_EXTRA_FILTER",
            name="No extra filter",
            description="Basstrategi utan extra professionellt filter.",
            category="Baseline",
            apply=lambda df, market_df=None: _bool_series(df, True),
        ),
        ResearchFilter(
            id="PRICE_ABOVE_10",
            name="Price > 10",
            description="Undviker mycket billiga aktier.",
            category="Liquidity",
            apply=lambda df, market_df=None: df["Close"] > 10,
        ),
        ResearchFilter(
            id="DOLLAR_VOLUME_20M",
            name="Dollar Volume > 20M",
            description="Kräver rimlig institutionell likviditet.",
            category="Liquidity",
            apply=lambda df, market_df=None: (df["Close"] * df["Volume"]).rolling(20).mean() > 20_000_000,
        ),
        ResearchFilter(
            id="DOLLAR_VOLUME_50M",
            name="Dollar Volume > 50M",
            description="Striktare likviditetsfilter.",
            category="Liquidity",
            apply=lambda df, market_df=None: (df["Close"] * df["Volume"]).rolling(20).mean() > 50_000_000,
        ),
        ResearchFilter(
            id="VOLUME_ABOVE_MA20",
            name="Volume > MA20",
            description="Kräver högre volym än 20-dagars snitt vid entry.",
            category="Volume",
            apply=lambda df, market_df=None: df["Volume"] > df["Volume"].rolling(20).mean(),
        ),
        ResearchFilter(
            id="VOLUME_150_MA20",
            name="Volume > 150% MA20",
            description="Kräver tydlig volymexpansion.",
            category="Volume",
            apply=lambda df, market_df=None: df["Volume"] > df["Volume"].rolling(20).mean() * 1.5,
        ),
        ResearchFilter(
            id="MARKET_ABOVE_MA200",
            name="Market > MA200",
            description="Handlar bara när SPY är över MA200.",
            category="Market Regime",
            apply=lambda df, market_df=None: _aligned_market_close(df, market_df) > _sma(_aligned_market_close(df, market_df), 200),
        ),
        ResearchFilter(
            id="MARKET_ABOVE_MA50",
            name="Market > MA50",
            description="Handlar bara när SPY är över MA50.",
            category="Market Regime",
            apply=lambda df, market_df=None: _aligned_market_close(df, market_df) > _sma(_aligned_market_close(df, market_df), 50),
        ),
        ResearchFilter(
            id="CLOSE_ABOVE_EMA21",
            name="Close > EMA21",
            description="Kräver positiv kortsiktig trend.",
            category="Trend",
            apply=lambda df, market_df=None: df["Close"] > _ema(df["Close"], 21),
        ),
        ResearchFilter(
            id="EMA21_SLOPE_UP",
            name="EMA21 slope up",
            description="Kräver stigande EMA21.",
            category="Trend",
            apply=lambda df, market_df=None: _ema(df["Close"], 21) > _ema(df["Close"], 21).shift(5),
        ),
        ResearchFilter(
            id="MA50_SLOPE_UP",
            name="MA50 slope up",
            description="Kräver stigande MA50.",
            category="Trend",
            apply=lambda df, market_df=None: _sma(df["Close"], 50) > _sma(df["Close"], 50).shift(10),
        ),
        ResearchFilter(
            id="NEAR_52W_HIGH_5",
            name="Within 5% of 52W high",
            description="Striktare närhet till 52-veckorshögsta.",
            category="Momentum",
            apply=lambda df, market_df=None: df["Close"] >= df["High"].rolling(252).max() * 0.95,
        ),
        ResearchFilter(
            id="ATR_PCT_2_10",
            name="ATR% between 2 and 10",
            description="Undviker både döda och extremt volatila aktier.",
            category="Volatility",
            apply=lambda df, market_df=None: ((_atr(df, 14) / df["Close"] * 100) >= 2) & ((_atr(df, 14) / df["Close"] * 100) <= 10),
        ),
        ResearchFilter(
            id="ATR_PCT_BELOW_8",
            name="ATR% below 8",
            description="Undviker för hög volatilitet.",
            category="Volatility",
            apply=lambda df, market_df=None: (_atr(df, 14) / df["Close"] * 100) < 8,
        ),
    ]


def get_filter_by_id(filter_id: str) -> ResearchFilter:
    for item in professional_filter_library():
        if item.id == filter_id:
            return item
    raise KeyError(f"Unknown research filter: {filter_id}")
