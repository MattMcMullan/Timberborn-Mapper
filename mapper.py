#!/usr/bin/env python3
import argparse
import sys
import json
import math
import random
import uuid
from dataclasses import dataclass
from typing import List, Optional
from PIL import Image

#  __  __           ___                   _   
# |  \/  |__ _ _ __| __|__ _ _ _ __  __ _| |_ 
# | |\/| / _` | '_ \ _/ _ \ '_| '  \/ _` |  _|
# |_|  |_\__,_| .__/_|\___/_| |_|_|_\__,_|\__|
#             |_|                             
# Map Format

class TimberbornSize(dict):
    def __init__(self, X: int, Y: int):
        dict.__init__(self, X=X, Y=Y)

class TimberbornArray(dict):
    def __init__(self, Array: List[object]):
        array_str = ''
        for element in Array:
            array_str += f'{element} '

        dict.__init__(self, Array=array_str)

class TimberbornMapSize(dict):
    def __init__(self, Size: TimberbornSize):
        dict.__init__(self, Size=Size)

class TimberbornTerrainMap(dict):
    def __init__(self, Heights: TimberbornArray):
        dict.__init__(self, Heights=Heights)

class TimberbornSoilMoistureSimulator(dict):
    def __init__(self, MoistureLevels: TimberbornArray):
        dict.__init__(self, MoistureLevels=MoistureLevels)

class TimberbornWaterMap(dict):
    def __init__(self, WaterDepths: TimberbornArray, Outflows: TimberbornArray):
        dict.__init__(self, WaterDepths=WaterDepths, Outflows=Outflows)

class TimberbornSingletons(dict):
    def __init__(
        self,
        MapSize: TimberbornMapSize,
        SoilMoistureSimulator: TimberbornSoilMoistureSimulator,
        TerrainMap: TimberbornTerrainMap,
        WaterMap: TimberbornWaterMap,
    ):
        dict.__init__(
            self,
            MapSize=MapSize,
            SoilMoistureSimulator=SoilMoistureSimulator,
            TerrainMap=TerrainMap,
            WaterMap=WaterMap,
        )

class TimberbornEntity(dict):
    def __init__(self, TemplateName:str):
        id = f'{uuid.uuid4()}'
        dict.__init__(self, Id=id, TemplateName=TemplateName)

class TimberbornCoordinates(dict):
    def __init__(self, X: int, Y: int, Z: int):
        dict.__init__(self, X=X, Y=Y, Z=Z)

class TimberbornOrientation(dict):
    def __init__(self, Value: str = 'Cw0'):
        dict.__init__(self, Value=Value)

class TimberbornBlockObject(dict):
    def __init__(self, Coordinates: TimberbornCoordinates, Orientation: TimberbornOrientation):
        dict.__init__(self, Coordinates=Coordinates, Orientation=Orientation)

class TimberbornGrowable(dict):
    def __init__(self, GrowthProgress: float = 1.0):
        dict.__init__(self, GrowthProgress=GrowthProgress)

class TimberbornCoordinatesOffset(dict):
    def __init__(self, X: float, Y: float):
        dict.__init__(self, X=X, Y=Y)

class TimberbornCoordinatesOffseter(dict):
    def __init__(self, CoordinatesOffset: TimberbornCoordinatesOffset):
        dict.__init__(self, CoordinatesOffset=CoordinatesOffset)
    
    @classmethod
    def random(cls) -> 'TimberbornCoordinatesOffseter':
        return cls(TimberbornCoordinatesOffset(random.random() * 0.25, random.random() * 0.25))

class TimberbornNaturalResourceModelRandomizer(dict):
    def __init__(self, Rotation: float, DiameterScale: float, HeightScale: float):
        dict.__init__(self, Rotation=Rotation, DiameterScale=DiameterScale, HeightScale=HeightScale)

    @classmethod
    def random(cls, scale: float) -> 'TimberbornNaturalResourceModelRandomizer':
        return TimberbornNaturalResourceModelRandomizer(
            random.random() * 360,
            0.25 + scale,
            0.25 + scale,
        )

class TimberbornYielderCuttable(dict):
    def __init__(self, Id: str, Amount: int):
        dict.__init__(
            self,
            Yield={
                "Good": {
                    "Id": Id,
                },
                "Amount": Amount,
            }
        )

class TimberbornWateredObject(dict):
    def __init__(self, IsDry: bool):
        dict.__init__(self, IsDry=IsDry)

class TimberbornLivingNaturalResource(dict):
    def __init__(self, IsDead: bool):
        dict.__init__(self, IsDead=IsDead)

class TimberbornGrowable(dict):
    def __init__(self, GrowthProgress: float = 1.0):
        dict.__init__(self, GrowthProgress=GrowthProgress)

class TimberbornPrioritizable(dict):
    def __init__(self, Priority="Normal"):
        dict.__init__(self, Priority={"Value": Priority})

class TimberbornTreeComponents(dict):
    def __init__(
        self,
        BlockObject: TimberbornBlockObject,
        CoordinatesOffseter: TimberbornCoordinatesOffseter,
        Growable: TimberbornGrowable,
        LivingNaturalResource: TimberbornLivingNaturalResource,
        NaturalResourceModelRandomizer: TimberbornNaturalResourceModelRandomizer,
        WateredObject: TimberbornWateredObject,
        YielderCuttable: TimberbornYielderCuttable,
    ):
        dict.__init__(
            self,
            BlockObject=BlockObject,
            BuilderJob={},
            CoordinatesOffseter=CoordinatesOffseter,
            Demolishable={},
            Growable=Growable,
            LivingNaturalResource=LivingNaturalResource,
            NaturalResourceModelRandomizer=NaturalResourceModelRandomizer,
            Prioritizable=TimberbornPrioritizable(),
            WateredObject=WateredObject,
        )
        self['Yielder:Cuttable'] = YielderCuttable
        self['Inventory:GoodStack'] = {"Storage": {"Goods": []}}

class TimberbornPineTree(TimberbornEntity):
    def __init__(self, Components: TimberbornTreeComponents):
        TimberbornEntity.__init__(self, "Pine")
        self["Components"] = Components

class TimberbornMap(dict):
    def __init__(
        self,
        GameVersion: str,
        Singletons: TimberbornSingletons,
        Entities: List[TimberbornEntity],
    ):
        dict.__init__(
            self,
            GameVersion=GameVersion,
            Singletons=Singletons,
            Entities=Entities
        )


#  ___                     _  _                    _ _         _   _          
# |_ _|_ __  __ _ __ _ ___| \| |___ _ _ _ __  __ _| (_)_____ _| |_(_)___ _ _  
# | || '  \/ _` / _` / -_) .` / _ \ '_| '  \/ _` | | |_ / _` |  _| / _ \ ' \ 
# |___|_|_|_\__,_\__, \___|_|\_\___/_| |_|_|_\__,_|_|_/__\__,_|\__|_\___/_||_|
#               |___/                                                        
# Image Normalization

def read_monochrome_image(filename: str, width: int, height: int) -> Image.Image:
    image = Image.open(filename)
    print(f'Image Size: {image.size}')

    image = image.convert('I')
    if width > 0:
        print(f'Adjusting width to {width}')
        image = image.resize((width, image.height))

    if height > 0:
        print(f'Adjusting height to {height}')
        image = image.resize((image.width, height))
    
    return image

#  _  _     _      _   _                   
# | || |___(_)__ _| |_| |_ _ __  __ _ _ __ 
# | __ / -_) / _` | ' \  _| '  \/ _` | '_ \
# |_||_\___|_\__, |_||_\__|_|_|_\__,_| .__/
#            |___/                   |_|   
# Heightmap

@dataclass
class Heightmap:
    min_height: int
    max_height: int
    width: int
    height: int
    data: List[int]

    @property
    def map_size(self) -> TimberbornMapSize:
        return TimberbornMapSize(TimberbornSize(self.width, self.height))
    
    @property
    def terrain_map(self) -> TimberbornTerrainMap:
        return TimberbornTerrainMap(TimberbornArray(self.data))

    def get(self, x: int, y: int) -> int:
        assert(x < self.width)
        assert(y < self.height)
        return self.data[x + y * self.width]

def read_heightmap(width: int, height: int, min_height: int, max_height: int, filename: str) -> Heightmap:
    output_range = max_height - min_height

    print(f'\nReading Heightmap')
    image = read_monochrome_image(filename, width, height)
    image_min = min(image.getdata())
    image_max = max(image.getdata())
    image_range = image_max - image_min
    print(f'Image Min: {image_min}')
    print(f'Image Max: {image_max}')
    height_data = []
    for pixel in image.getdata():
        normalized = (pixel - image_min)/image_range
        height = round(normalized * output_range + min_height)
        height_data.append(height)

    return Heightmap(
        min_height=min_height,
        max_height=max_height,
        width=image.size[0],
        height=image.size[1],
        data=height_data,
    )

# __      __    _           __  __           
# \ \    / /_ _| |_ ___ _ _|  \/  |__ _ _ __ 
#  \ \/\/ / _` |  _/ -_) '_| |\/| / _` | '_ \
#   \_/\_/\__,_|\__\___|_| |_|  |_\__,_| .__/
#                                      |_|   
# Water Map

@dataclass
class WaterMap:
    depths: List[float]
    moisture: List[float]
    width: int
    height: int
    
    @property
    def water_map(self) -> TimberbornWaterMap:
        return TimberbornWaterMap(TimberbornArray(self.depths), TimberbornArray(['0:0:0:0'] * self.width * self.height))

    @property
    def soil_moisture_simulator(self) -> TimberbornSoilMoistureSimulator:
        return TimberbornSoilMoistureSimulator(TimberbornArray(self.moisture))

    def get(self, x: int, y: int) -> int:
        assert(x < self.width)
        assert(y < self.height)
        return self.depths[x + y * width]

def read_water_map(heightmap: Heightmap, filename: Optional[str]) -> Heightmap:
    if filename is None:
        return WaterMap(
            [0] * heightmap.width * heightmap.height,
            [0] * heightmap.width * heightmap.height,
            heightmap.width,
            heightmap.height
        )

    print(f'\nReading Water Map')
    image = read_monochrome_image(filename, heightmap.width, heightmap.height)
    image_min = min(image.getdata())
    image_max = max(image.getdata())
    image_range = image_max - image_min
    print(f'Image Min: {image_min}')
    print(f'Image Max: {image_max}')
    depths = []
    for pixel in image.getdata():
        normalized = (pixel - image_min)/image_range
        depths.append(round(normalized))

    # Generate a soil moisture map from the water map
    distance: List[List[float]] = []
    for x in range(image.width):
        row = []
        for y in range(image.height):
            if depths[x + y * image.height] > 0:
                row.append(0)
            else:
                row.append(100)
        distance.append(row)
    
    def transfer_value(x: int, y: int, dx: int, dy: int) -> float:
        if x + dx < 0 or x + dx >= image.height or y + dy < 0 or y + dy >= image.height:
            return 100

        horizontal = abs(dx) + abs(dy)
        if horizontal == 2:
            horizontal = 1.41

        za = heightmap.get(x, y)
        zb = heightmap.get(x + dx, y + dy)
        vertical = abs(za - zb) * 4
        return distance[x+dx][y+dy] + horizontal + vertical

    for i in range(16):
        for x in range(image.width):
            for y in range(image.height):
                min_distance = distance[x][y]
                for dx in [-1, 0, 1]:
                    for dy in [-1, 0, 1]:
                        min_distance = min(min_distance, transfer_value(x, y, dx, dy))
                distance[x][y] = min_distance

    moisture = []
    for x in range(image.width):
        for y in range(image.height):
            moisture.append(max(16-distance[y][x], 0))

    return WaterMap(
        depths,
        moisture,
        image.size[0],
        image.size[1]
    )

#  _____            __  __           
# |_   _| _ ___ ___|  \/  |__ _ _ __ 
#  | || '_/ -_) -_) |\/| / _` | '_ \
#  |_||_| \___\___|_|  |_\__,_| .__/
#                             |_|   
# Tree Map

@dataclass
class Tree:
    x: int
    y: int
    z: int
    size: float
    alive: bool

@dataclass
class TreeMap:
    trees: List[Tree]

    @property
    def entities(self) -> List[TimberbornEntity]:
        entities: List[TimberbornEntity] = []
        for tree in self.trees:
            entities.append(
                TimberbornPineTree(
                    Components=TimberbornTreeComponents(
                        BlockObject=TimberbornBlockObject(
                            Coordinates=TimberbornCoordinates(X=tree.x, Y=tree.y, Z=tree.z),
                            Orientation=TimberbornOrientation(),
                        ),
                        CoordinatesOffseter=TimberbornCoordinatesOffseter.random(),
                        Growable=TimberbornGrowable(1.0),
                        LivingNaturalResource=TimberbornLivingNaturalResource(IsDead=not tree.alive),
                        NaturalResourceModelRandomizer=TimberbornNaturalResourceModelRandomizer.random(tree.size),
                        WateredObject=TimberbornWateredObject(IsDry=not tree.alive),
                        YielderCuttable=TimberbornYielderCuttable(Id="Log", Amount=2),
                    )
                )
            )
        return entities

def read_tree_map(heightmap: Heightmap, water_map: WaterMap, treeline_cutoff: float, filename: Optional[str]):
    if filename is None:
        return TreeMap([])

    print(f'\nReading Treemap')
    image = read_monochrome_image(filename, heightmap.width, heightmap.height)
    image_min = min(image.getdata())
    image_max = max(image.getdata())
    print(f'Image Min: {image_min}')
    print(f'Image Max: {image_max}')
    image_range = image_max - image_min

    trees = []
    for i, pixel in enumerate(image.getdata()):
        normalized = (pixel - image_min)/image_range
        if normalized > treeline_cutoff:
            z = heightmap.data[i]
            y = math.floor(i / image.width)
            x = i - y * image.width
            alive = water_map.moisture[i] > 0
            trees.append(Tree(x, y, z, normalized, alive))

    print(f"Made {len(trees)} trees. {100 * len(trees)/(image.width * image.height):.2f}% tree coverage.")
    return TreeMap(trees)

#  __  __      _      
# |  \/  |__ _(_)_ _  
# | |\/| / _` | | ' \ 
# |_|  |_\__,_|_|_||_|
# Main                    

def main() -> None:
    parser = argparse.ArgumentParser(description='Convert a heightmap into a Timberborn custom map.')
    parser.add_argument('--output', type=str, help='Path to output the resulting map to.')

    parser.add_argument('--heightmap', type=str, help='Path to a grayscale heightmap image.')
    parser.add_argument('--min-height', type=int, help='Soil depth at the lowest point in the heightmap.', default=3)
    parser.add_argument('--max-height', type=int, help='Soil depth at the highest point in the heightmap.', default=13)
    parser.add_argument('--width', type=int, help='Width of the resulting map.', default=-1)
    parser.add_argument('--height', type=int, help='Height of the resulting map.', default=-1)

    parser.add_argument('--treemap', type=str, help='Path to a grayscale treemap image.', default=None)
    parser.add_argument('--treeline-cutoff', type=float, help='Relative pixel intensity under which trees will not spawn.', default=0.2)

    parser.add_argument('--water-map', type=str, help='Path to a grayscale water map image.', default=None)
    args = parser.parse_args()

    heightmap = read_heightmap(width=args.width, height=args.height, min_height=args.min_height, max_height=args.max_height, filename=args.heightmap)
    water_map = read_water_map(heightmap, args.water_map)
    tree_map = read_tree_map(heightmap, water_map, args.treeline_cutoff, args.treemap)

    singletons = TimberbornSingletons(
        MapSize=heightmap.map_size,
        SoilMoistureSimulator=water_map.soil_moisture_simulator,
        TerrainMap=heightmap.terrain_map,
        WaterMap=water_map.water_map,
    )
    map = TimberbornMap("0", singletons, tree_map.entities)
    with open(args.output, 'w') as f:
        json.dump(map, f, indent=4)

if __name__ == '__main__':
    main()