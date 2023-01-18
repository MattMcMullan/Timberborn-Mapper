# Timberborn-Mapper
A tool for turning heightmaps into Timberborn maps.

# Setup
1. Install python. You can find it [here](https://www.python.org/downloads/).
2. Install pillow. You can read their instructions [here](https://pillow.readthedocs.io/en/stable/installation.html), or just open your command prompt and run "python -m pip install pillow".
3. Click the green "Code" button in github for directions to download this code.

## Windows binary
Windows users can try script packaged as single exectutable file from [dist directory](dist/).
No dependecies or setup required.
Copy examples dir if needed.

## Alternatively (for advanced python users)
Using poetry

1. clone repository
2. install [poetry](https://python-poetry.org/docs/)
3. `poetry install` will install all dependecies from `pyproject.toml` and manages virtual environment
4. `poetry shell` activates virtual environment for the project

Currently project requires python 3.10 or 3.11 but may work on other versions.

# Usage

**Note**: at the moment treemap will generate only birches, other trees need fixing yield attributes.

- script expcets a grayscale image as heightmap (most likely a PNG but some other formats should also work)
- check help for available options, like setting map size, output file name and script behaviour modifiers

## Script version
- Open the command prompt and cd to the directory with the code.
- Run `python mapper --help` to see instructions on how to use it.

## Binary version (Windows)
- Open command promt (or powershell) and cd to the folder with exectutable.
- Run `TimberbornMapper.exe --help` to see instructions on how to use it.

You can also just drag-n-drop heightmap image or spec file onto exectutable's icon or it's links. But can't set options directly this way.
It will output **.timber** file into same place where inpiut file was taken.

## Configuration files

**Note**: Script is using tomllib for config format, so it will work only on python **3.11+** (Windows binary uses 3.11).

If configuration is available script will try to write a template config into system-specific config dir.

If file already exists it will try to read it. Command-line arguments should override config values when set.


## Getting heightmaps

There are likely a number of services where you can get a heightmap of real or fictional location.

One I've used so far is https://heightmap.skydark.pl/
- It has map size slider limited to 17 km, but you can input it down to 9 km (lesser doesn't work for me for some reason).
- Select desired area and click "Download PNG height map".
- If picture lacks contrast play with "Height scale" input slider.

# TODO

1. ~~Make a Windows binary for players who don't care for python, pip or java alternavely.~~
2. More interactivity.
3. More validation and better error handling.
4. Document some example method where and how you can get heightmap image of real-world location.
5. Try to automatically save to <User>/Documents/Timberborn/Maps/ on Windows
6. Implement configurations (WIP)
7. Disable colors by env vars
8. Fix plant Yields
9. Add chestnut trees
