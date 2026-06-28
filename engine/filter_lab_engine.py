"""
EdgeCraft Quant Lab
Filter Lab Engine

Ansvar:
- Hantera AI Research Engine-logik
- Sammanställa Filter Lab-resultat
- Rangordna filter
- Skapa enkelt handelsrecept

Version: 1.0
"""

from typing import Dict, List


class FilterLabEngine:

    def __init__(self):
        self.results = []

    def reset(self):
        """Rensa tidigare tester."""
        self.results = []

    def add_result(self, result: Dict):
        """Lägg till ett filterresultat."""
        self.results.append(result)

    def get_results(self) -> List[Dict]:
        """Returnera alla resultat."""
        return self.results

    def rank_filters(self) -> List[Dict]:
        """Sortera bästa filter överst."""

        return sorted(
            self.results,
            key=lambda x: (
                x.get("Score Delta", 0),
                x.get("PF Delta", 0),
                -x.get("DD Delta", 0)
            ),
            reverse=True,
        )

    def improvements(self):

        return [
            r for r in self.results
            if r.get("Approved", False)
        ]

    def declines(self):

        return [
            r for r in self.results
            if not r.get("Approved", False)
        ]

    def build_trade_recipe(
        self,
        base_recipe: Dict,
        recommended_filters: List[str]
    ) -> Dict:

        recipe = dict(base_recipe)

        recipe["Recommended Filters"] = recommended_filters

        return recipe

    def generate_summary(self):

        return {
            "tested_filters": len(self.results),
            "approved": len(self.improvements()),
            "rejected": len(self.declines()),
        }