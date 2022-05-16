import matplotlib.pyplot as plt
from os import path
import pandas as pd

def main(dir):
    df = pd.read_csv('../logfile.csv')
    plot_all_single(df)
    #hourly_gr = df.gr / df.speed * 3600

def plot_all_single(df):
    plot_vec("gr", df.gr, df.time, "days", "growth rate in gramm/seconds", False, "black")
    plot_vec("sr", df.sr, df.time, "days", "starch rate in gramm/seconds", False, "magenta")
    plot_vec("leaf_mass", df.leaf_mass, df.time, "days", "leaf mass (gDW)", False, "green")
    plot_vec("stem_mass", df.stem_mass, df.time, "days", "stem mass (gDW)", False, "yellow")
    plot_vec("root_mass", df.root_mass, df.time, "days", "root mass (gDW)", False, "red")
    plot_vec("starch_mass", df.starch_mass, df.time, "days", "starch mass (gDW)", False, "black")
    plot_vec("water_pool", df.water, df.time, "days", "water (mol)", False, "gray")
    plot_vec("nitrate_pool", df.nitrate, df.time, "days", "nitrate (mol)", False, "cyan")
    # plot_all(df)

def plot_vec(name,vec, time, xlabel=None, ylabel=None, plot=False, color="black"):
    seconds = time / 1000 * 240
    minutes = seconds / 60
    hours = minutes / 60
    days = hours / 24
    #print(seconds, minutes, hours, days)
    plt.plot(days, vec,color=color)
    if xlabel:
        plt.xlabel(xlabel)
    if ylabel:
        plt.ylabel(ylabel)
    if plot:
        plt.show()
    plt.savefig("{}.svg".format(name))
    plt.close()

def plot_all(df):
    fig, axs = plt.subplots(len(df.columns),figsize=(10,30),sharex=True)
    fig
    time = df.time
    for i in range(0,len(df.columns)):
        axs[i].plot(time, df[df.columns[i]])
    plt.savefig("plot.svg")
    plt.show()
    plt.close()

if __name__ == "__main__":
    main('')