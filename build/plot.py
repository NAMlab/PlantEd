import matplotlib.pyplot as plt

def main():
    with open("../logs/2021-11-17 18.52.02Generic Plant/gametime.txt", "r") as f:
        lines = f.readlines()
    gametimes = [float(l.strip())/1000 for l in lines]

    with open("../logs/2021-11-17 18.52.02Generic Plant/growth.txt", "r") as f:
        lines = f.readlines()
    growth_rates = [float(l.strip()) for l in lines]

    with open("../logs/2021-11-17 18.52.02Generic Plant/starch.txt", "r") as f:
        lines = f.readlines()
    starch = [float(l.strip()) for l in lines]

    with open("../logs/2021-11-17 18.52.02Generic Plant/gamespeed.txt", "r") as f:
        lines = f.readlines()
    gamespeeds = [float(l.strip()) for l in lines]

    with open("../logs/2021-11-17 18.52.02Generic Plant/water.txt", "r") as f:
        lines = f.readlines()
    waters = [float(l.strip()) for l in lines]

    with open("../logs/2021-11-17 18.52.02Generic Plant/nitrate.txt", "r") as f:
        lines = f.readlines()
    nitrates = [float(l.strip()) for l in lines]

    with open("../logs/2021-11-17 18.52.02Generic Plant/leaf_mass.txt", "r") as f:
        lines = f.readlines()
    leaf_mass = [float(l.strip()) for l in lines]

    with open("../logs/2021-11-17 18.52.02Generic Plant/stem_mass.txt", "r") as f:
        lines = f.readlines()
    stem_mass = [float(l.strip()) for l in lines]

    with open("../logs/2021-11-17 18.52.02Generic Plant/root_mass.txt", "r") as f:
        lines = f.readlines()
    root_mass = [float(l.strip()) for l in lines]

    with open("../logs/2021-11-17 18.52.02Generic Plant/starch_pool.txt", "r") as f:
        lines = f.readlines()
    starch_pool = [float(l.strip()) for l in lines]

    actual_gr = []
    for i in range (0,len(growth_rates)):
        rate = growth_rates[i] / gamespeeds[i]
        actual_gr.append(rate)

    plt.figure(figsize=(16, 8))
    plt.subplot(421)
    plt.plot(gametimes, actual_gr)
    plt.xlabel("time in s")
    plt.ylabel("gr")

    #plt.plot(gametimes, growth_rates, "r")
    plt.subplot(422)
    plt.plot(gametimes, waters, "b")
    plt.xlabel("time in s")
    plt.ylabel("water in mol")

    plt.subplot(423)
    plt.plot(gametimes, starch, "b")
    plt.xlabel("time in s")
    plt.ylabel("starch in mol")

    plt.subplot(424)
    plt.plot(gametimes, nitrates, "g")
    plt.xlabel("time in s")
    plt.ylabel("nitrate in mol")

    plt.subplot(425)
    plt.plot(gametimes, leaf_mass, "g")
    plt.ylabel("leaf_mass in g")
    plt.subplot(426)
    plt.plot(gametimes, stem_mass, "r")
    plt.ylabel("stem_mass in g")
    plt.subplot(427)
    plt.plot(gametimes, root_mass, "b")
    plt.ylabel("root_mass in g")
    plt.subplot(428)
    plt.plot(gametimes, starch_pool, "b")
    plt.ylabel("starch_pool in g")

    plt.show()


if __name__ == "__main__":
    main()