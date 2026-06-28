from strategies.registry import get_strategy_config


class StrategyRunner:
    """
    Gemensam motor som kör valfri strategi från Strategy Registry.
    Alla moduler (Backtest, Research, Walk Forward, Monte Carlo,
    Scanner, AI Lab) ska använda denna klass.
    """

    def __init__(self, strategy_name):
        self.strategy_name = strategy_name
        self.config = get_strategy_config(strategy_name)

    def apply_signals(self, data, **parameters):
        """
        Kör strategins signalfunktion.
        """

        signal_function = self.config["signal_function"]

        default_parameters = self.config["default_parameters"].copy()

        default_parameters.update(parameters)

        return signal_function(
            data=data,
            **default_parameters
        )

    def get_default_parameters(self):
        return self.config["default_parameters"]

    def get_parameter_grid(self):
        return self.config["parameter_grid"]

    def get_name(self):
        return self.strategy_name