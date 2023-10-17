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

## Usage

After installation using pip, PlantEd can be started as a command line program. The exact usage can be seen in the following.
```commandline
$ PlantEd --help

usage: PlantEd [-h] [-v] [--logFile] [--windowed] [--noUI]

options:
  -h, --help        show this help message and exit
  -v , --logLevel   Set the detail of the log events (default: WARNING)
  --logFile         The folder where all log files will be stored. The log files inside this folder will be overwritten. The Folder will be created automatically. By default, no folders or logfiles are created.
  --windowed        Should start the PlantEd full screen or windowed. Setting this flag results in a windowed start.
  --noUI            noUI flag ensures that only the server is started. Please refer to the console for the port and interface used.

```

## Development 
PlantEd can be installed as an editable package using pip for development
purposes. To do this, execute the following command in the cloned repository: 

```commandline
pip install -e .
```
The requirements.txt contains all necessary packages for the development. Using conda, a new enviroment can be easily created:
```commandline
conda create --name PlantEd
```
and all listed packages can be installed in this environment:
```commandline
pip install -r requirements.txt
```

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