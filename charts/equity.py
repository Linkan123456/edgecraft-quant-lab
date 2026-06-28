import matplotlib.pyplot as plt


def plot_equity_curve(df, title: str):
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(df.index, df["Equity"])
    ax.set_title(title)
    ax.grid(True)
    return fig