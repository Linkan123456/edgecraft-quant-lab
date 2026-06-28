from abc import ABC, abstractmethod


class BaseStrategy(ABC):
    """
    Basklass för alla strategier i EdgeCraft Quant Lab.

    Alla strategier ska ärva från denna klass.
    """

    name = "Unnamed Strategy"
    version = "1.0"
    description = ""
    asset_classes = []
    tags = []

    @abstractmethod
    def generate_signals(self, data, **parameters):
        """
        Returnerar DataFrame med köp-/säljsignaler.
        """
        pass

    @abstractmethod
    def default_parameters(self):
        """
        Returnerar strategins standardparametrar.
        """
        pass

    @abstractmethod
    def parameter_grid(self):
        """
        Returnerar parametrar som används av Research Engine.
        """
        pass

    def metadata(self):
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "asset_classes": self.asset_classes,
            "tags": self.tags,
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