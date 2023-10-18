import matplotlib.pyplot as plt
import numpy
import numpy as np
import pandas as pd
import pygame

from PlantEd_Server.data import assets


def generate_png_from_vec(vector_list, name_list, colors, ticks, xlabel, ylabel, path_to_logs, filename, color="dark_background") -> pygame.Surface:
    # make a Figure and attach it to a canvas.
    plt.style.use(color)

    fig, ax = plt.subplots()
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    days = ticks / (1000*24*60*60)

    for vector, name, color in zip(vector_list, name_list, colors):
        ax.plot(days, vector, label="{}".format(name), color=color)
    ax.legend(loc='upper right')

    plt.savefig(path_to_logs + "/" + filename)
    image = pygame.image.load(path_to_logs + "/" + filename).convert_alpha()

    return image