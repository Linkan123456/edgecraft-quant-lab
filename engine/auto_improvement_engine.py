import itertools
import pandas as pd


DEFAULT_PARAMETER_GRID = {
    "stop_loss_atr": [0.5, 0.75, 1.0],
    "risk_reward": [2.0, 2.5, 3.0],
}


def build_improvement_grid(existing_grid=None):
    grid = {}

    if existing_grid:
        grid.update(existing_grid)

    for key, values in DEFAULT_PARAMETER_GRID.items():
        if key not in grid:
            grid[key] = values

    return grid


def generate_parameter_sets(parameter_grid):
    keys = list(parameter_grid.keys())

    values = [
        parameter_grid[k]
        for k in keys
    ]

    for combo in itertools.product(*values):
        yield dict(zip(keys, combo))


def append_parameter_sets(results_df, parameter_sets):
    if results_df is None or results_df.empty:
        return results_df

    rows = []

    for params in parameter_sets:
        for _, row in results_df.iterrows():

            r = row.copy()

            for key, value in params.items():
                r[key] = value

            rows.append(r)

    return pd.DataFrame(rows)


def run_auto_improvement(results_df, existing_parameter_grid=None):

    parameter_grid = build_improvement_grid(existing_parameter_grid)

    parameter_sets = list(
        generate_parameter_sets(parameter_grid)
    )

    improved_df = append_parameter_sets(
        results_df,
        parameter_sets
    )

    return {
        "parameter_grid": parameter_grid,
        "parameter_sets": parameter_sets,
        "results": improved_df,
        "total_tests": len(parameter_sets)
    }