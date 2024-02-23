import matplotlib.pyplot as plt
import numpy
import numpy as np
import pandas as pd
import pygame

from PlantEd.data import assets


def generate_png_from_vec(vector_list, name_list, colors, ticks, xlabel, ylabel, path_to_logs, filename, color="dark_background") -> pygame.Surface:
    # make a Figure and attach it to a canvas.
    plt.style.use(color)

    fig, ax = plt.subplots()
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    days = ticks

    for vector, name, color in zip(vector_list, name_list, colors):
        ax.plot(days, vector, label="{}".format(name), color=color)
    ax.legend(loc='upper right')

    plt.savefig(path_to_logs + "/" + filename)
    image = pygame.image.load(path_to_logs + "/" + filename).convert_alpha()
    return image

def generate_small_plot(df, id, path_to_logs) -> pygame.Surface:
    plt.style.use("dark_background")
    fig, ax = plt.subplots()
    ax.set_xlabel("time")
    ax.set_ylabel("biomass")

    ax.plot(df.time, df.leaf_biomass, label="leaf", color="g")
    ax.plot(df.time, df.stem_biomass, label="stem", color="b")
    ax.plot(df.time, df.root_biomass, label="root", color="r")
    ax.plot(df.time, df.seed_biomass, label="seed", color="m")

    ax.legend(loc='upper right')

    plt.savefig(f"{path_to_logs}/{id}.PNG")
    image = pygame.image.load(f"{path_to_logs}/{id}.PNG").convert_alpha()
    plt.close(fig)
    return image


def generate_big_plot(df, path_to_logs=None):
    fig, ax = plt.subplots(10, figsize=(10,15), layout="constrained")

    days = df.time

    ax[0].plot(days, df.temperature)
    ax[0].set_ylabel("Temperature", rotation=0, labelpad=65)

    ax[1].plot(days, df.humidity)
    ax[1].set_ylabel("humidity", rotation=0, labelpad=65)

    ax[2].plot(days, df.sun_intensity)
    ax[2].set_ylabel("sun_intensity", rotation=0, labelpad=65)

    ax[3].plot(days, df.precipitation)
    ax[3].set_ylabel("precipitation", rotation=0, labelpad=65)

    ax[4].plot(days, df.water_pool)
    ax[4].set_ylabel("water_pool", rotation=0, labelpad=65)

    ax[5].plot(days, df.accessible_water)
    ax[5].set_ylabel("accessible_water", rotation=0, labelpad=65)

    ax[6].plot(days, df.accessible_nitrate)
    ax[6].set_ylabel("accessible_nitrate", rotation=0, labelpad=65)

    ax[7].plot(days, df.leaf_percent, label="leaf_percent")
    ax[7].plot(days, df.stem_percent, label="stem_percent")
    ax[7].plot(days, df.root_percent, label="root_percent")
    ax[7].plot(days, df.seed_percent, label="seed_percent")
    ax[7].set_ylabel("growth_percent", rotation=0, labelpad=65)
    ax[7].legend(loc='upper right')

    ax[8].plot(days, df.leaf_biomass, label="leaf_biomass")
    ax[8].plot(days, df.stem_biomass, label="stem_biomass")
    ax[8].plot(days, df.root_biomass, label="root_biomass")
    ax[8].plot(days, df.seed_biomass, label="seed_biomass")
    ax[8].set_ylabel("biomass", rotation=0, labelpad=65)
    ax[8].legend(loc='upper right')

    ax[9].plot(days, df.starch_pool)
    ax[9].set_ylabel("starch_pool", rotation=0, labelpad=65)

    #plt.show()
    plt.savefig("7.PNG")
    #image = pygame.image.load(path_to_logs + "/plot.PNG").convert_alpha()
    #return image


if __name__ == "__main__":
    import pandas
    path = "~/PlantEd/src/PlantEd/client/data/finished_games/Sunny Gigglezap1702900252.9989524"
    df = pandas.read_csv("7.csv")
    generate_big_plot(df, path)

#def make_subplot(plot, vec, time, name, color, xlabel, ylabel) -> plt.Subplot:
