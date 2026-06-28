# charts/research_dashboard.py
# EdgeCraft Quant Lab v0.56

import matplotlib.pyplot as plt


def plot_profit_factor_distribution(df):
    fig, ax = plt.subplots(figsize=(6, 4))

    values = df["Profit Factor"].replace(999, 5)

    ax.hist(values, bins=20)

    ax.set_title("Profit Factor")
    ax.set_xlabel("PF")
    ax.set_ylabel("Antal")

    plt.tight_layout()

    return fig


def plot_return_distribution(df):
    fig, ax = plt.subplots(figsize=(6, 4))

    ax.hist(df["Total Return"], bins=20)

    ax.set_title("Total Return")

    ax.set_xlabel("%")

    ax.set_ylabel("Antal")

    plt.tight_layout()

    return fig


def plot_drawdown_distribution(df):
    fig, ax = plt.subplots(figsize=(6, 4))

    ax.hist(df["Max Drawdown"], bins=20)

    ax.set_title("Max Drawdown")

    ax.set_xlabel("%")

    ax.set_ylabel("Antal")

    plt.tight_layout()

    return fig


def plot_edgecraft_distribution(df):
    fig, ax = plt.subplots(figsize=(6, 4))

    ax.hist(df["EdgeCraft Score"], bins=20)

    ax.set_title("EdgeCraft Score")

    ax.set_xlabel("Score")

    ax.set_ylabel("Antal")

    plt.tight_layout()

    return fig


def plot_walkforward_distribution(df):
    fig, ax = plt.subplots(figsize=(6, 4))

    ax.bar(
        ["Pass", "Fail"],
        [
            len(df[df["Test Pass"] == True]),
            len(df[df["Test Pass"] == False])
        ]
    )

    ax.set_title("Walk Forward")

    plt.tight_layout()

    return fig