# PlantEd
RTS Simulation, Plant Survival Game


Download the game at:
https://danielkoch.itch.io/planted

![Image of Plant](src/PlantEd/data/assets/plant_complete.png)

## Troubleshooting
#### libGL error
If you receive a message that says something like the following :
```commandline
libGL error: MESA-LOADER: failed to open swrast: ...
```

Try installing libstdcxx-ng from conda-forge if you are using [Conda](https://conda.io/).
```commandline
conda install -c conda-forge libstdcxx-ng
```


See [this discussion](https://stackoverflow.com/a/71421355) for the explanation, more information, and other possible solutions.