from itertools import product


def run_parameter_experiment(
    parameter_grid: dict,
    callback
):
    """
    Kör alla kombinationer av parametrar.

    callback(params) ska returnera ett resultat.
    """

    keys = list(parameter_grid.keys())
    values = list(parameter_grid.values())

    results = []

    for combination in product(*values):

        params = dict(zip(keys, combination))

        result = callback(params)

        results.append(result)

    return results