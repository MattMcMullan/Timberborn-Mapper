#  _____            __  __
# |_   _| _ ___ ___|  \/  |__ _ _ __
#  | || '_/ -_) -_) |\/| / _` | '_ \
#  |_||_| \___\___|_|  |_\__,_| .__/
#                             |_|
# Tree Map
import math
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List, Optional

from image_utils import MapImage
from maps.format import (
    TimberbornBlockObject,
    TimberbornCoordinates,
    TimberbornCoordinatesOffseter,
    TimberbornEntity,
    TimberbornGrowable,
    TimberbornLivingNaturalResource,
    TimberbornNaturalResourceModelRandomizer,
    TimberbornOrientation,
    TimberbornTree,
    TimberbornTreeComponents,
    TimberbornWateredObject,
    TimberbornYielderCuttable,
)

from .heightmap import Heightmap
from .watermap import WaterMap


class TreeSpecies(Enum):
    birch = ("Birch", 1)
    pine = ("Pine", 2)
    maple = ("Maple", 3)


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
            entities.append(
                TimberbornTree(
                    species=tree.species.value[0],
                    Components=TimberbornTreeComponents(
                        BlockObject=TimberbornBlockObject(
                            Coordinates=TimberbornCoordinates(X=tree.x, Y=tree.y, Z=tree.z),
                            Orientation=TimberbornOrientation(),
                        ),
                        CoordinatesOffseter=TimberbornCoordinatesOffseter.random(),
                        Growable=TimberbornGrowable(1.0),
                        LivingNaturalResource=TimberbornLivingNaturalResource(IsDead=not tree.alive),
                        NaturalResourceModelRandomizer=TimberbornNaturalResourceModelRandomizer.random(),
                        WateredObject=TimberbornWateredObject(IsDry=not tree.alive),
                        YielderCuttable=TimberbornYielderCuttable(Id="Log", Amount=tree.species.value[1]),
                    ),
                )
            )
        return entities


@dataclass
class ImageToTimberbornTreemapSpec:
    filename: str
    treeline_cutoff: float = 0.1
    birch_cutoff: float = 0.4
    pine_cutoff: float = 0.7


def read_tree_map(heightmap: Heightmap, water_map: WaterMap, path: Path, spec: Optional[ImageToTimberbornTreemapSpec]):
    if spec is None:
        return TreeMap([])

    print(f"\nReading Treemap")
    filepath = path / spec.filename

    map_image = MapImage(filepath, heightmap.width, heightmap.height)
    image = map_image.image

    trees = []
    for i, pixel in enumerate(map_image.normalized_data):
        if pixel < spec.treeline_cutoff:
            continue

        z = heightmap.data[i]
        y = math.floor(i / image.width)
        x = i - y * image.width
        alive = water_map.moisture[i] > 0
        species = TreeSpecies.maple
        if pixel < spec.birch_cutoff:
            species = TreeSpecies.birch
        elif pixel < spec.pine_cutoff:
            species = TreeSpecies.pine
        trees.append(Tree(species, x, y, z, alive))

    print(f"Made {len(trees)} trees. {100 * len(trees)/(image.width * image.height):.2f}% tree coverage.")
    return TreeMap(trees)
