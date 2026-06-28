# charts/walk_forward_dashboard.py
# EdgeCraft Quant Lab v0.58

import matplotlib.pyplot as plt


def plot_test_score_by_window(df):
    fig, ax = plt.subplots(figsize=(8, 4))

    ax.plot(df["Window"], df["Test Score"], marker="o")

    ax.set_title("Walk Forward Test Score per fönster")
    ax.set_xlabel("Fönster")
    ax.set_ylabel("Test Score")

    plt.tight_layout()

    return fig


def plot_test_return_by_window(df):
    fig, ax = plt.subplots(figsize=(8, 4))

    ax.bar(df["Window"], df["Test Total Return"])

    ax.set_title("Test Return per fönster")
    ax.set_xlabel("Fönster")
    ax.set_ylabel("Return %")

    plt.tight_layout()

    return fig


def plot_test_profit_factor_by_window(df):
    fig, ax = plt.subplots(figsize=(8, 4))

    values = df["Test Profit Factor"].replace(999, 5)

    ax.bar(df["Window"], values)

    ax.set_title("Test Profit Factor per fönster")
    ax.set_xlabel("Fönster")
    ax.set_ylabel("Profit Factor")

    plt.tight_layout()

    return fig


def plot_test_pass_fail(df):
    fig, ax = plt.subplots(figsize=(6, 4))

    pass_count = len(df[df["Test Pass"] == True])
    fail_count = len(df[df["Test Pass"] == False])

    ax.bar(
        ["Pass", "Fail"],
        [pass_count, fail_count]
    )

    ax.set_title("Walk Forward Pass / Fail")
    ax.set_ylabel("Antal fönster")

    plt.tight_layout()

    return fig