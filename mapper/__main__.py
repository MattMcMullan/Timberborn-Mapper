#!/usr/bin/env python3
import argparse
import json
import logging
import re
import sys
from dataclasses import dataclass
from enum import Enum
from hashlib import sha1
from pathlib import Path
from platform import python_version
# from subprocess import run
from time import time
from typing import Any, Optional, Union
from zipfile import ZIP_DEFLATED, ZipFile

import colorama
from appdirs import AppDirs
from maps.format import TimberbornMap, TimberbornSingletons
from maps.heightmap import ImageToTimberbornHeightmapLinearConversionSpec, ImageToTimberbornHeightmapSpec, read_heightmap
from maps.treemap import ImageToTimberbornTreemapSpec, read_tree_map
from maps.watermap import read_water_map

try:
    import tomllib
except ModuleNotFoundError:
    TOML_AVAILABLE = False
else:
    TOML_AVAILABLE = True

#  __  __      _
# |  \/  |__ _(_)_ _
# | |\/| / _` | | ' \
# |_|  |_\__,_|_|_||_|
# Main

__version__ = "0.3.5-a-4"

APPNAME = "TimberbornMapper"
APP_AUTHOR = "MattMcMullan"
CONFIG_FILE = "mapperconf.toml"

# This is a config template, not source of config defaults. Use MapperConfig __init__ instead
DEFAULT_TOML = """[main]
config_version = 1
nocolor = false
non_interactive = false
keep_json = false
maps_dir = ""

[map]
max_map_size_defualt = -1
max_map_size_limit = 1024
max_elevation_default = -1
max_elevation_limit = 64
game_version = ""
"""


class MapperConfig(argparse.Namespace):
    _os_dict = {
        "windows": "w",
        "unknown": "w",  # not like we have many valid options
        "macos": "m",
        "linux": "w"     # change if game supports Linux _natively_
    }

    def __init__(self, skip_values=["", "DEFAULT"], **kwargs):
        self._skip_values = skip_values

        self.maps_dir = ""
        self.max_map_size_defualt = 256
        self.max_map_size_limit = 1024
        self.max_elevation_default = 16
        self.max_elevation_limit = 64
        self.nocolor = False
        self.non_interactive = False
        self.keep_json = False

        self._os_key = self.get_os()
        self._os_letter = self._os_dict[self._os_key]
        self.game_version = f"0.3.5.0-c1e2fcc-s{self._os_letter}"

        self._safe_extend(skip_values, **kwargs)

    def get_os(self):
        key = "unknown"
        if sys.platform.startswith("linux"):
            key = "linux"
        elif sys.platform.startswith("win") or sys.platform.startswith("cygwin"):
            key = "windows"
        elif sys.platform.startswith("darwin"):
            key = "macos"
        return key

    def guess_game_dir(self, user=""):
        path = None
        if self._os_key in ("windows", "macos", "linux"):
            path = Path(f"~{user}/Documents/Timberborn/")
        if path:
            path = path.expanduser()
            logging.debug(f"Game Dir: '{path}'")
            if path.is_dir():
                return path
        return None

    def _safe_extend(self, skip_values, **kwargs):
        for key, val in kwargs.items():
            if (val not in skip_values) and (key[0] != "_"):
                setattr(self, key, val)

    """
    def load_defaults(self, **kwargs):
         for key, val in kwargs.items():
            if (key[0] != "_") and not hasattr(self, key):
                setattr(self, key, val)
    """

    def update_extend(self, **kwargs):
        """extend self attributes overriding existing if value is not in skip_values"""
        if "_skip_values" in kwargs:
            skip_values = kwargs.pop("_skip_values")
        else:
            skip_values = self._skip_values

        self._safe_extend(skip_values, **kwargs)


class GameDefs(Enum):
    """ Game default values and properties """
    MAP_SUFFIX = ".timber"
    MAX_ELEVATION = 16
    MAX_MAP_SIZE = 256


R = colorama.Style.RESET_ALL
H1 = colorama.Fore.BLUE
# H2 = colorama.Fore.GREEN
BOLD = colorama.Style.BRIGHT
CODE = colorama.Back.WHITE + colorama.Fore.BLACK


@dataclass
class ImageToTimberbornWatermapSpec:
    filename: str


class ImageToTimberbornSpec:
    def __init__(
        self,
        heightmap: Union[ImageToTimberbornHeightmapSpec, dict],
        width: int = -1,  # XXX should use optional instead of sentinel value
        height: int = -1,
        treemap: Union[Optional[ImageToTimberbornTreemapSpec], dict] = None,
        watermap: Union[Optional[ImageToTimberbornWatermapSpec], dict] = None,
    ):
        self.width = width
        self.height = height

        if isinstance(heightmap, dict):
            heightmap = ImageToTimberbornHeightmapSpec(**heightmap)
        self.heightmap = heightmap

        if isinstance(treemap, dict):
            treemap = ImageToTimberbornTreemapSpec(**treemap)
        self.treemap = treemap

        if isinstance(watermap, dict):
            watermap = ImageToTimberbornWatermapSpec(**watermap)
        self.watermap = watermap

    width: int
    height: int
    heightmap: ImageToTimberbornHeightmapSpec
    treemap: Optional[ImageToTimberbornTreemapSpec]
    watermap: Optional[ImageToTimberbornWatermapSpec]


def image_to_timberborn(spec: ImageToTimberbornSpec, path: Path, output_path: Path, args: Any) -> Path:

    logging.info(f"Output dir: `{output_path.parent}`")

    t = -time()
    heightmap = read_heightmap(width=spec.width, height=spec.height, spec=spec.heightmap, path=path)
    logging.info(f"Finished in {t + time():.2f} sec.")

    t = -time()
    if spec.watermap is None:
        water_map = read_water_map(heightmap, None, None)
    else:
        water_map = read_water_map(heightmap, filename=spec.watermap.filename, path=path)
    logging.info(f"Finished water map in {t + time():.2f} sec.")

    t = -time()
    tree_map = read_tree_map(heightmap, water_map, spec=spec.treemap, path=path)
    logging.info(f"Finished tree map in {t + time():.2f} sec.")

    singletons = TimberbornSingletons(
        MapSize=heightmap.map_size,
        SoilMoistureSimulator=water_map.soil_moisture_simulator,
        TerrainMap=heightmap.terrain_map,
        WaterMap=water_map.water_map,
    )
    timber_map = TimberbornMap(args.game_version, singletons, tree_map.entities)

    data = json.dumps(heightmap.terrain_map)
    maphash = sha1(data.encode('utf-8')).hexdigest()
    logging.debug(f"Terrain data hash: sha1 {maphash}")

    try:
        with open(output_path, "w") as f:
            json.dump(timber_map, f, indent=4)
    except (OSError, PermissionError) as exc:
        logging.error(
            " ! Couldn't write to output path due to following error:"
            "(Perhaps output path is incorrect or has permission denied)"
        )
        raise exc
    else:
        logging.debug(output_path)
        timber_path = output_path.with_suffix(".timber")
        arcname = output_path.with_suffix(".json").name
        print(f"Zipping '{arcname}'")
        with ZipFile(timber_path, "w", compression=ZIP_DEFLATED, compresslevel=8) as timberzip:
            timberzip.write(output_path, arcname=arcname)
        if args.keep_json:
            target = output_path.parent / f"{output_path.stem}-mapper{maphash[:8]}.json"
            output_path.rename(target)
            logging.debug(f"Unzipped file store as '{target}'")
        else:
            output_path.unlink()
        print(f"\nSaved to '{timber_path}'\nYou can now open it in Timberborn map editor to add finishing touches.")
    return timber_path


def make_output_path(args: Any) -> Path:
    output_path = args.output
    if output_path:
        if output_path.suffix != GameDefs.MAP_SUFFIX.value:
            logging.warning(f"Output extension ('{output_path.suffix}') is not '{GameDefs.MAP_SUFFIX.value}'"
                            f" it will be changed automatically.")
    elif args.maps_dir:
        output_path = Path(args.maps_dir) / args.input.with_suffix('.tmp').name
    else:
        output_path = args.input.with_suffix(".tmp")
    if not output_path.is_absolute():
        output_path = Path.cwd() / output_path
    return output_path


def manual_image_to_timberborn(args: Any) -> None:
    treemap = None
    if args.treemap is not None:
        treemap = ImageToTimberbornTreemapSpec(
            filename=args.treemap,
            treeline_cutoff=args.treeline_cutoff,
            birch_cutoff=args.birch_cutoff,
            pine_cutoff=args.pine_cutoff,
        )

    watermap = None
    if args.water_map is not None:
        watermap = ImageToTimberbornWatermapSpec(
            filename=args.water_map,
        )

    output_path = make_output_path(args)

    image_to_timberborn(
        ImageToTimberbornSpec(
            width=args.width,
            height=args.height,
            heightmap=ImageToTimberbornHeightmapSpec(
                filename=args.input,
                linear_conversion=ImageToTimberbornHeightmapLinearConversionSpec(
                    min_height=args.min_elevation, max_height=args.max_elevation
                ),  # if not args.bucketize_heightmap else None,
                # ImageToTimberbornHeightmapBucketizedConversionSpec() if args.bucketize_heightmap else None,
                bucketized_conversion=None,
            ),
            treemap=treemap,
            watermap=watermap,
        ),
        args.input.parent,
        output_path,
        args,
    )


def specfile_to_timberborn(args: Any) -> None:
    with open(args.input, "r") as f:
        specdict = json.load(f)

    output_path = make_output_path(args)
    image_to_timberborn(ImageToTimberbornSpec(**specdict), args.input.parent, output_path, args)


def build_parser() -> argparse.ArgumentParser:
    # try to guess script name ('python mapper' vs 'TimberbornMapper.exe')
    script = "mapper"
    for arg in sys.argv:
        if arg.lower().endswith('.exe'):
            script = Path(arg).name
            break

    description = (
        f"Tool for importing heightmap images as Timberborn custom maps.\n"
        f"\n  {BOLD}HOW TO USE:{R}\n\n"
        f" Script has 2 modes: {BOLD}manual{R} and {BOLD}specfile{R}\n"
        f" - {BOLD}Manual{R} mode takes as input a path to an heightmap (image) file and a number of options\n"
        f" - {BOLD}Specfile{R} mode pulls all map option from a json-formatted file, commandline map options are\n"
        f" ignored.\n"
        f" Mode is set by checking input file extension.\n\n"
        f" If you are using a binary version you can just {BOLD}drag-n-drop{R} image or spec file on executable or it's link.\n"
        f" (but then you can't set options directly)\n\n"
        f' Run "{BOLD}{script} --help{R}" to see manual mode and generic options. \n'
        f" like desired map height and width or base elevation. It can also take separate tree and water maps.\n\n"
        f" Try example command:\n"
        f" {CODE}{script} m examples/alpine_lakes/height.png --min-height 4 --width 128 --height 128{R}\n"
        f" Output will be zipped JSON file with {H1}{BOLD}{GameDefs.MAP_SUFFIX.value}{R} extension that should be ready to be"
        f"  opened with {BOLD}{H1}map editor{R}."
    )

    parser = argparse.ArgumentParser(
        description=description,
        formatter_class=argparse.RawTextHelpFormatter,
    )

    parser.add_argument("input", type=Path, help="Path to a heightmap image or json spec file")
    parser.add_argument(
        "--output", type=Path, help="Path to output the resulting map to. Defaults to input file name, with timber ext."
    )

    parser.add_argument(
        "--min-elevation", "--min-height", "--low", type=int,
        help="Soil elevation at the lowest point in the heightmap. Defaults to 3.", default=3,
    )
    parser.add_argument(
        "--max-elevation", "--max-height", "--high", type=int,
        help=f"Soil elevation at the highest point in the heightmap. Defaults to {GameDefs.MAX_ELEVATION.value}.",
        default=GameDefs.MAX_ELEVATION.value
    )
    # parser.add_argument(
    #     "--bucketize-heightmap",
    #     action="store_true",
    #     help=("Use a specific proportion of height values rather than linearly interpolating the image value"
    #           " between the min and max height. Use a spec file to specify non-default bucket weights."),
    # )
    parser.add_argument("--width", type=int, help="Width of the resulting map. Defaults to image width.", default=-1)
    parser.add_argument("--height", type=int, help="Height of the resulting map. Defaults to image height.", default=-1)

    parser.add_argument("--treemap", type=str, help="Path to a grayscale treemap image.", default=None)
    parser.add_argument(
        "--treeline-cutoff",
        type=float,
        help="Relative pixel intensity under which trees will not spawn. Defaults to 0.1.",
        default=0.1,
    )
    parser.add_argument(
        "--birch-cutoff",
        type=float,
        help="Relative pixel intensity under which trees will spwan as birch trees. Defaults to 0.2.",
        default=0.4,
    )
    parser.add_argument(
        "--pine-cutoff",
        type=float,
        help="Relative pixel intensity under which trees will spwan as pine trees. Defaults to 0.7.",
        default=0.7,
    )

    parser.add_argument("--water-map", type=str, help="Path to a grayscale water map image. None by default.", default=None)

    parser.add_argument('-c', '--confpath', type=str, default='',
                        help="Path to config file. Will use default location if empty. '0' to disable.")
    parser.add_argument('--open-config', action='store', dest='open_config',
                        nargs='?', const='vi', default=False,
                        help="Open config file with editor, editor command as argument or vi as default")

    parser.add_argument('--keep-json', action='store_true', default='DEFAULT', help="Do not remove map .json after packing")
    # parser.add_argument('--write-config', action="store_true", help='Write (overwrite) config file at defualt location.')
    parser.add_argument('-l', '--loglevel', choices=('debug', 'info', 'warning', 'error', 'critical'), default='info',
                               help='Control additional output verbosity')
    # parser.add_argument('-C', '--nocolor', action="store_true", default='DEFAULT', help='Disable usage of colors in console')

    parser.add_argument('-I', '--non-interactive', action='store_true', default='DEFAULT', help="Disable interactions")

    return parser


def main() -> None:
    t = -time()
    colorama.init()

    args = build_parser().parse_args()
    config = MapperConfig(skip_values=["", "DEFAULT", -1])

    # configure logging
    loglevel = getattr(args, "loglevel", "INFO").upper()
    logging.basicConfig(
        level=getattr(logging, loglevel),
        format=f'{H1}%(levelname)s{R}: %(message)s'
    )
    print(f"{BOLD}Timberborn Mapper{R} ver. {H1}{BOLD}{__version__}{R} running on python {H1}{python_version()}{R}")

    """
    if TOML_AVAILABLE:
        if args.open_config:
            run([args.open_config, str(config_path)])
            sys.exit(0)

    """

    if args.confpath == "0":
        logging.debug("config reading is disabled by options")
        # config.read_dict(DEFUALT_CONF)
    elif TOML_AVAILABLE:
        if args.confpath:
            config_path = Path(args.confpath)
        else:
            app_dirs = AppDirs(APPNAME, APP_AUTHOR)
            config_path = Path(app_dirs.user_config_dir) / CONFIG_FILE

        if config_path.is_file():
            logging.debug(f"reading config file from '{config_path}'")
            with open(config_path, "rb") as f:
                toml_config = tomllib.load(f)
                for title, section in toml_config.items():
                    config.update_extend(**section)
        else:
            if args.confpath:
                logging.critical(f"Can't read config file - it doesn't exist or not a file: '{config_path}'")
                sys.exit("Couldn't read configuration")
            else:
                try:
                    toml_config = tomllib.loads(DEFAULT_TOML)
                    for title, section in toml_config.items():
                        config.update_extend(**section)
                    config_path.parent.mkdir(parents=True, exist_ok=True)

                    toml_str = DEFAULT_TOML

                    if not config.non_interactive:
                        guessed_game_dir = config.guess_game_dir()
                        if guessed_game_dir:
                            answer = None
                            print(f"Found game directory at '{guessed_game_dir}'")
                            while answer not in ('y', 'n', '0', '1'):
                                answer = input("Add it's 'Maps/' into config file? (Y/n or 0/1) > ")
                                if answer:
                                    answer = str(answer).strip().lower()[0]
                            if answer in ('1', 'y'):
                                toml_str = re.sub(
                                    '^maps_dir = [\"\']{2}',
                                    f'maps_dir = "{guessed_game_dir / "Maps/"}"',
                                    toml_str,
                                    flags=re.M
                                )

                    with open(config_path, "w") as f:
                        f.write(toml_str)
                except tomllib.TOMLDecodeError as exc:
                    logging.error(f"Error in default TOML configuration, please contact authors: {exc}")
                except (OSError, PermissionError) as exc:
                    logging.error(f"Couln't write config file to '{config_path}', probably permissions or path issue: {exc}")
                else:
                    logging.info(f"Created defualt config file: '{config_path}'")
    else:
        logging.warning("tomllib is not available (it's included in python 3.11+) reading configuration files is disabled")

    config.update_extend(_skip_values=["DEFAULT"], **vars(args))
    # config building is done

    logging.debug(f"OS detected as {config._os_key.title()} mapper will set GameVersion as {config.game_version}")

    # from pprint import pprint
    # pprint(vars(config))
    # print("-- dir --")
    # pprint(dir(config))

    if not config.input.is_absolute():
        config.input = Path.cwd() / config.input

    logging.info(f"Input path: `{config.input}`")

    if not config.input.is_file():
        sys.exit(f"Path `{config.input}` is not a file or not accessible. Please check it and try again.")

    # wrapping execution in exception catcher to halt window form closing in interactive mode
    try:
        if config.input.suffix.lower() == ".json":
            logging.info("JSON file will be processed as spec file")
            specfile_to_timberborn(config)
        else:
            logging.info("File will be verified and processed like an image")
            manual_image_to_timberborn(config)
    except Exception as exc:
        logging.critical("Exception happened!")
        if not config.non_interactive:
            logging.critical("Following error happened during execution:")
            logging.critical(exc)
            input('(Press enter to throw traceback and exit. Run from console to see details if window closes)')
        raise exc

    t += time()
    if not config.non_interactive:
        input('(Press enter to exit)')
    logging.info(f"Total execution time: {t:.2f} sec.")


if __name__ == "__main__":
    main()
