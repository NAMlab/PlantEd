![Dynamic TOML Badge](https://img.shields.io/badge/dynamic/toml?url=https%3A%2F%2Fraw.githubusercontent.com%2FNAMlab%2FPlantEd%2Fmain%2Fpyproject.toml&query=%24.project.version&label=version)
![Python Version from PEP 621 TOML](https://img.shields.io/python/required-version-toml?tomlFilePath=https%3A%2F%2Fraw.githubusercontent.com%2FNAMlab%2FPlantEd%2Fmain%2Fpyproject.toml)
[![Linter](https://github.com/NAMlab/PlantEd/actions/workflows/lint.yml/badge.svg)](https://github.com/NAMlab/PlantEd/actions/workflows/lint.yml)
[![Tests](https://github.com/NAMlab/PlantEd/actions/workflows/tests.yml/badge.svg)](https://github.com/NAMlab/PlantEd/actions/workflows/tests.yml)
[![Build](https://github.com/NAMlab/PlantEd/actions/workflows/publish.yml/badge.svg)](https://github.com/NAMlab/PlantEd/actions/workflows/publish.yml)

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