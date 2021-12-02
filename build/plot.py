import matplotlib.pyplot as plt
from os import path

def main(dir):
    dir = dir

    with open(path.join(dir,"gametime.txt"), "r") as f:
        lines = f.readlines()
    gametimes = [float(l.strip())/1000 for l in lines]

    with open(path.join(dir,"growth.txt"), "r") as f:
        lines = f.readlines()
    growth_rates = [float(l.strip()) for l in lines]

    with open(path.join(dir,"starch.txt"), "r") as f:
        lines = f.readlines()
    starch = [float(l.strip()) for l in lines]

    with open(path.join(dir,"gamespeed.txt"), "r") as f:
        lines = f.readlines()
    gamespeeds = [float(l.strip()) for l in lines]

    with open(path.join(dir,"water.txt"), "r") as f:
        lines = f.readlines()
    waters = [float(l.strip()) for l in lines]

    with open(path.join(dir,"nitrate.txt"), "r") as f:
        lines = f.readlines()
    nitrates = [float(l.strip()) for l in lines]

    with open(path.join(dir,"leaf_mass.txt"), "r") as f:
        lines = f.readlines()
    leaf_mass = [float(l.strip()) for l in lines]

    with open(path.join(dir,"stem_mass.txt"), "r") as f:
        lines = f.readlines()
    stem_mass = [float(l.strip()) for l in lines]

    with open(path.join(dir,"root_mass.txt"), "r") as f:
        lines = f.readlines()
    root_mass = [float(l.strip()) for l in lines]

    with open(path.join(dir,"starch_pool.txt"), "r") as f:
        lines = f.readlines()
    starch_pool = [float(l.strip()) for l in lines]

    actual_gr = []
    for i in range (0,len(growth_rates)):
        rate = growth_rates[i] / gamespeeds[i] if gamespeeds[i] != 0 else growth_rates[i] /1
        actual_gr.append(rate)

    plt.figure(figsize=(16, 8))
    plt.subplot(321)
    plt.plot(gametimes, actual_gr)
    plt.xlabel("time in s")
    plt.ylabel("gr")

    #plt.plot(gametimes, growth_rates, "r")
    plt.subplot(322)
    plt.plot(gametimes, waters, "b")
    plt.xlabel("time in s")
    plt.ylabel("water in mol")

    plt.subplot(323)
    plt.plot(gametimes, starch, "b")
    plt.xlabel("time in s")
    plt.ylabel("starch in mol")

    plt.subplot(324)
    plt.plot(gametimes, nitrates, "g")
    plt.xlabel("time in s")
    plt.ylabel("nitrate in mol")

    plt.subplot(325)
    plt.plot(gametimes, starch_pool, "b")
    plt.ylabel("starch_pool in g")

    plt.subplot(326)
    plt.plot(gametimes, leaf_mass, "g")
    plt.ylabel("leaf_mass in g")
    plt.plot(gametimes, stem_mass, "r")
    plt.ylabel("stem_mass in g")
    plt.plot(gametimes, root_mass, "b")
    plt.ylabel("root_mass in g")


    #plt.show()
    plt.savefig(path.join(dir,'plot.png'))


if __name__ == "__main__":
    main('')