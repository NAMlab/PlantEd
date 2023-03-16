import matplotlib.pyplot as plt
from os import path
import pandas as pd


def main(path="../logfile.csv", logname="log"):
    df = pd.read_csv(path)
    plot_all_single(df, logname)
    # hourly_gr = df.gr / df.speed * 3600


def plot_all_single(df, logname):
    plot_vec(
        logname,
        "leaf_rate",
        df.leaf_rate / df.speed,
        df.time,
        "days",
        "leaf_rate in gramm/seconds",
        False,
        "black",
    )
    plot_vec(
        logname,
        "stem_rate",
        df.stem_rate / df.speed,
        df.time,
        "days",
        "stem_rate in gramm/seconds",
        False,
        "black",
    )
    plot_vec(
        logname,
        "growth_rates",
        df.root_rate / df.speed,
        df.time,
        "days",
        "root_rate in gramm/seconds",
        False,
        "black",
    )
    plot_vec(
        logname,
        "sr",
        df.sr / df.speed / 1000,
        df.time,
        "days",
        "starch rate in mmol/seconds",
        False,
        "magenta",
    )
    plot_vec(
        logname,
        "leaf_mass",
        df.leaf_mass,
        df.time,
        "days",
        "leaf mass gDW",
        False,
        "green",
    )
    plot_vec(
        logname,
        "stem_mass",
        df.stem_mass,
        df.time,
        "days",
        "stem mass gDW",
        False,
        "yellow",
    )
    plot_vec(
        logname,
        "root_mass",
        df.root_mass,
        df.time,
        "days",
        "root mass gDW",
        False,
        "red",
    )
    plot_vec(
        logname,
        "starch_mass",
        df.starch_mass / 1000,
        df.time,
        "days",
        "starch mass mmol",
        False,
        "black",
    )
    plot_vec(
        logname,
        "water_pool",
        df.water / 1000,
        df.time,
        "days",
        "water mmol",
        False,
        "gray",
    )
    plot_vec(
        logname,
        "nitrate_pool",
        df.nitrate / 1000,
        df.time,
        "days",
        "nitrate mmol",
        False,
        "cyan",
    )
    # plot_all(df)


def plot_vec(
    logname,
    name,
    vec,
    time,
    xlabel=None,
    ylabel=None,
    plot=False,
    color="black",
):
    seconds = time / 1000
    minutes = seconds / 60
    hours = minutes / 60
    days = hours / 24
    # print(seconds, minutes, hours, days)
    plt.plot(days, vec, color=color)
    if xlabel:
        plt.xlabel(xlabel)
    if ylabel:
        plt.ylabel(ylabel)
    if plot:
        plt.show()
    plt.savefig("../logs/{}/{}.png".format(logname, name))
    plt.close()


def plot_all(df):
    fig, axs = plt.subplots(len(df.columns), figsize=(10, 30), sharex=True)
    fig
    time = df.time
    for i in range(0, len(df.columns)):
        axs[i].plot(time, df[df.columns[i]])
    plt.savefig("plot.png")
    plt.show()
    plt.close()


if __name__ == "__main__":
    main(path="../logs/6.csv", logname="6")
