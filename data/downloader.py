import yfinance as yf
import pandas as pd


def load_market_data(ticker: str, start, end, interval: str) -> pd.DataFrame:
    data = yf.download(
        ticker,
        start=start,
        end=end,
        interval=interval,
        auto_adjust=True,
        progress=False
    )

    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    return data.dropna()