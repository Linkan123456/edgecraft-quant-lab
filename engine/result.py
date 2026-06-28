from dataclasses import dataclass
import pandas as pd


@dataclass
class BacktestResult:
    strategy: str
    parameters: dict
    equity: pd.DataFrame
    trades: pd.DataFrame
    stats: dict
    market: str = ""
    timeframe: str = ""
    metadata: dict = None

    def is_valid(self):
        return self.equity is not None and self.stats is not None

    def trade_count(self):
        if self.trades is None or self.trades.empty:
            return 0
        return len(self.trades)

    def get_stat(self, key, default=None):
        return self.stats.get(key, default)