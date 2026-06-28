from strategies.double_seven import DoubleSevenStrategy
from strategies.oops_reversal import OOPSReversalStrategy
from strategies.professional_pullback import ProfessionalPullbackStrategy


STRATEGY_REGISTRY = {
    "Double Seven": DoubleSevenStrategy(),
    "OOPS Reversal": OOPSReversalStrategy(),
    "Professional Pullback": ProfessionalPullbackStrategy(),
}


def get_strategy_names():
    return list(STRATEGY_REGISTRY.keys())


def get_strategy(strategy_name):
    return STRATEGY_REGISTRY[strategy_name]


def get_strategy_config(strategy_name):
    strategy = get_strategy(strategy_name)

    return {
        "signal_function": strategy.generate_signals,
        "default_parameters": strategy.default_parameters(),
        "parameter_grid": strategy.parameter_grid(),
        "metadata": strategy.metadata()
    }