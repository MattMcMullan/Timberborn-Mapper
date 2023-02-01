#  _____            __  __
# |_   _| _ ___ ___|  \/  |__ _ _ __
#  | || '_/ -_) -_) |\/| / _` | '_ \
#  |_||_| \___\___|_|  |_\__,_| .__/
#                             |_|
# Tree Map
import logging
import math
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List, Optional

from image_utils import MapImage
from maps.format import (TimberbornBlockObject, TimberbornCoordinates, TimberbornCoordinatesOffseter, TimberbornEntity,
                         TimberbornGrowable, TimberbornLivingNaturalResource, TimberbornNaturalResourceModelRandomizer,
                         TimberbornOrientation, TimberbornTree, TimberbornTreeComponents, TimberbornWateredObject,
                         TimberbornYielderCuttable, TimberbornGatherableYieldGrower, TimberbornYielderGatherable)

from .heightmap import Heightmap
from .watermap import WaterMap


class Goods(Enum):
    PineResin = "PineResin"
    Log = "Log"
    MapleSyrup = "MapleSyrup"
    Chestnut = "Chestnut"


class TreeSpecies(Enum):
    birch = ("Birch", {"logs": 1, "gth_good": None})
    pine = ("Pine", {"logs": 2, "gth_good": Goods.PineResin, "gth_amount": 2})
    maple = ("Maple", {"logs": 8, "gth_good": Goods.MapleSyrup, "gth_amount": 3})
    chestnut = ("ChestnutTree", {"logs": 4, "gth_good": Goods.Chestnut, "gth_amount": 3})


@dataclass
class Tree:
    species: TreeSpecies
    x: int
    y: int
    z: int
    alive: bool


@dataclass
class TreeMap:
    trees: List[Tree]

    @property
    def entities(self) -> List[TimberbornEntity]:
        entities: List[TimberbornEntity] = []
        for tree in self.trees:
            species_dict = tree.species.value[1]
            components_kwargs = {
                "BlockObject": TimberbornBlockObject(
                            Coordinates=TimberbornCoordinates(X=tree.x, Y=tree.y, Z=tree.z),
                            Orientation=TimberbornOrientation(),
                        ),
                "CoordinatesOffseter": TimberbornCoordinatesOffseter.random(),
                "Growable": TimberbornGrowable(1.0),
                "LivingNaturalResource": TimberbornLivingNaturalResource(IsDead=not tree.alive),
                "NaturalResourceModelRandomizer": TimberbornNaturalResourceModelRandomizer.random(),
                "WateredObject": TimberbornWateredObject(IsDry=not tree.alive),
                "YielderCuttable": TimberbornYielderCuttable(Id=Goods.Log.value, Amount=species_dict['logs']),
            }
            # add gatherables if tree has it
            gatherable_good = species_dict.get('gth_good', None)
            if gatherable_good:
                components_kwargs.update({
                    "GatherableYieldGrower": TimberbornGatherableYieldGrower(),  # TODO add growth randomization
                    "YielderGatherable": TimberbornYielderGatherable(
                                            Id=gatherable_good.value,
                                            Amount=species_dict.get("gth_amount", 1)
                                         )
                })

            entities.append(
                TimberbornTree(
                    species=tree.species.value[0],
                    Components=TimberbornTreeComponents(**components_kwargs),
                )
            )
        return entities


@dataclass
class ImageToTimberbornTreemapSpec:
    filename: str
    treeline_cutoff: float = 0.1
    birch_cutoff: float = 0.3
    pine_cutoff: float = 0.45
    chestnut_cutoff: float = 0.6


def read_tree_map(heightmap: Heightmap, water_map: WaterMap, path: Path, spec: Optional[ImageToTimberbornTreemapSpec]):
    if spec is None:
        return TreeMap([])

    print("\nReading Treemap")
    tree_counts = {}
    filepath = path / spec.filename

    map_image = MapImage(filepath, heightmap.width, heightmap.height)
    image = map_image.image

    logging.warning("!! Will generate only birches until Yeilds are fixed!")
    trees = []
    for i, pixel in enumerate(map_image.normalized_data):
        if pixel < spec.treeline_cutoff:
            continue

        z = heightmap.data[i]
        y = math.floor(i / image.width)
        x = i - y * image.width
        alive = water_map.moisture[i] > 0

        if pixel < spec.birch_cutoff:
            species = TreeSpecies.birch
        elif pixel < spec.pine_cutoff:
            species = TreeSpecies.pine
        elif pixel < spec.chestnut_cutoff:
            species = TreeSpecies.chestnut
        else:
            species = TreeSpecies.maple

        # species = TreeSpecies.birch  # WARNING DELETE ME when FIXED

        key = species.value[0]
        if key not in tree_counts.keys():
            tree_counts[key] = 1
        else:
            tree_counts[key] += 1

        trees.append(Tree(species, x, y, z, alive))

    logging.info(f"Made {len(trees)} trees. {100 * len(trees)/(image.width * image.height):.2f}% tree coverage.")
    for key, val in tree_counts.items():
        logging.debug(f"- {key: <8}: {val: >6}")
    return TreeMap(trees)
