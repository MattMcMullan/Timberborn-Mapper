#!/usr/bin/env python3
import argparse
import json
import logging
import sys
from dataclasses import dataclass
from enum import Enum
from hashlib import sha1
from pathlib import Path
from platform import python_version
from time import time
from typing import Any, Optional, Union
from zipfile import ZIP_DEFLATED, ZipFile

import colorama
from maps.format import TimberbornMap, TimberbornSingletons
from maps.heightmap import ImageToTimberbornHeightmapLinearConversionSpec, ImageToTimberbornHeightmapSpec, read_heightmap
from maps.treemap import ImageToTimberbornTreemapSpec, read_tree_map
from maps.watermap import read_water_map

#  __  __      _
# |  \/  |__ _(_)_ _
# | |\/| / _` | | ' \
# |_|  |_\__,_|_|_||_|
# Main

__version__ = "0.3.4-a-1"


class GameDefs(Enum):
    """ Game default values and properties """
    MAP_SUFFIX = ".timber"
    MAX_ELEVATION = 16
    MAX_MAP_SIZE = 256


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


def image_to_timberborn(spec: ImageToTimberbornSpec, path: Path, output_path: Path) -> Path:

    logging.info(f"output dir: `{output_path.parent}`")

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
    timber_map = TimberbornMap("0", singletons, tree_map.entities)

    if logging.root.level == logging.DEBUG:
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
        timber_path = output_path.with_suffix(".timber")
        arcname = output_path.with_suffix(".json").name
        print(f"\nZipping '{arcname}'")
        with ZipFile(timber_path, "w", compression=ZIP_DEFLATED, compresslevel=8) as timberzip:
            timberzip.write(output_path, arcname=arcname)
        # TODO conditional
        output_path.unlink()
        print(f"\nSaved to `{timber_path}`\nYou can now open it in Timberborn map editor to add finishing touches")
    return timber_path


def make_output_path(args: Any) -> Path:
    output_path = args.output
    if output_path:
        if output_path.suffix != GameDefs.MAP_SUFFIX.value:
            logging.warning(f" !output extension ('{output_path.suffix}') is not '{GameDefs.MAP_SUFFIX.value}'"
                            f" it will be changed automatically")
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
    )


def specfile_to_timberborn(args: Any) -> None:
    with open(args.input, "r") as f:
        specdict = json.load(f)

    output_path = make_output_path(args)
    image_to_timberborn(ImageToTimberbornSpec(**specdict), args.input.parent, output_path)


def main() -> None:

    colorama.init()
    R = colorama.Style.RESET_ALL
    H1 = colorama.Fore.BLUE
    # H2 = colorama.Fore.GREEN
    BOLD = colorama.Style.BRIGHT
    CODE = colorama.Back.WHITE + colorama.Fore.BLACK

    description = (
        f"Tool for importing heightmap images as Timberborn custom maps.\n"
        f"\n  {BOLD}HOW TO USE:{R}\n\n"
        f"It has 2 modes: '{H1}{BOLD}m{R}anual' and '{H1}{BOLD}s{R}pecfile'\n"
        f'Run "{BOLD}mapper m -h{R}" or "{BOLD}mapper s -h{R}" to see actual arguments for each mode.\n\n'
        f"Manual mode takes as input a path to an heightmap (image) file and a number of options\n"
        f"like desired map height and width or base elevation. It can also take separate tree and water maps.\n"
        f"Try example command:\n"
        f"> {CODE}mapper m examples/alpine_lakes/height.png --min-height 4 --width 128 --height 128{R}\n"
        f"Output will be zipped JSON file with {H1}{BOLD}{GameDefs.MAP_SUFFIX.value}{R} extension that should be ready to be"
        f" opened with {BOLD}{H1}map editor{R}."
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

    parser.add_argument('-l', '--loglevel', choices=('debug', 'info', 'warning', 'error', 'critical'), default='info',
                               help='control additional output verbosity')
    parser.add_argument('-C', '--nocolor', action="store_true", help='disable usage of colors in console')

    # parser.add_argument("input", type=Path, nargs='?', help="Path to a grayscale heightmap image.")

    """
    add_manual_image_to_timberborn_args(
        subparsers.add_parser(
            "manual-image-to-timberborn",
            help="Turn one or more specified images into a timberborn custom map.",
            aliases=["m", "man", "manual"],
            parents=[parent_parser]
        )
    )

    add_specfile_to_timberborn_args(
        subparsers.add_parser(
            "specfile-to-timberborn",
            help="Use a json specification to define how to turn images into a timberborn map.",
            aliases=["s", "spec", "specfile"],
            parents=[parent_parser]
        )
    )
    """
    # parser.add_argument("input", type=Path, nargs='?', help="Path to a grayscale heightmap image.")

    args = parser.parse_args()
    print(args)

    # configure logging
    loglevel = getattr(args, "loglevel", "INFO").upper()
    logging.basicConfig(
        level=getattr(logging, loglevel),
        format=f'{H1}%(levelname)s{R}: %(message)s'
    )

    if getattr(args, 'nocolor', False):
        colorama.init(strip=True)
    print(f"{BOLD}Timberborn Mapper{R} ver. {H1}{__version__}{R} running on python {H1}{python_version()}{R}")
    # logging.debug(Path(__file__).name)

    if not args.input.is_absolute():
        args.input = Path.cwd() / args.input

    logging.info(f"input path: `{args.input}`")

    if not args.input.is_file():
        sys.exit(f"Path `{args.input}` is not a file or not accessible. Please check it and try again.")

    if args.input.suffix.lower() == ".json":
        logging.info("JSON file will be processed as spec file")
        specfile_to_timberborn(args)
    else:
        logging.info("File will be verified and processed like an image")
        manual_image_to_timberborn(args)


if __name__ == "__main__":
    t = -time()
    main()
    t += time()
    print(f"\nTotal execution time: {t:.2f} sec.")
