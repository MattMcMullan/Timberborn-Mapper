# __      __    _           __  __
# \ \    / /_ _| |_ ___ _ _|  \/  |__ _ _ __
#  \ \/\/ / _` |  _/ -_) '_| |\/| / _` | '_ \
#   \_/\_/\__,_|\__\___|_| |_|  |_\__,_| .__/
#                                      |_|
# Water Map
import logging
from dataclasses import dataclass
from pathlib import Path
from time import time
from typing import List, Optional

from image_utils import MapImage
from maps.format import TimberbornArray, TimberbornSoilMoistureSimulator, TimberbornWaterMap

from .heightmap import Heightmap


@dataclass
class WaterMap:
    depths: List[float]
    moisture: List[float]
    width: int
    height: int

    @property
    def water_map(self) -> TimberbornWaterMap:
        return TimberbornWaterMap(TimberbornArray(self.depths), TimberbornArray(["0:0:0:0"] * self.width * self.height))

    @property
    def soil_moisture_simulator(self) -> TimberbornSoilMoistureSimulator:
        return TimberbornSoilMoistureSimulator(TimberbornArray(self.moisture))

    def get(self, x: int, y: int) -> int:
        assert x < self.width
        assert y < self.height
        return self.depths[x + y * self.width]


def read_water_map(heightmap: Heightmap, filename: Optional[str], path: Optional[Path]) -> Heightmap:

    if filename is None:
        return WaterMap(
            [0] * heightmap.width * heightmap.height,
            [0] * heightmap.width * heightmap.height,
            heightmap.width,
            heightmap.height,
        )
    else:
        filepath = path / filename

    print("\nReading Water Map")
    logging.debug(f"{filepath}")
    map_image = MapImage(filepath, heightmap.width, heightmap.height)
    depths = map_image.rounded_normalized_data
    image = map_image.image

    # Generate a soil moisture map from the water map
    logging.debug("Generating soil moisture map")
    logging.debug("Make distance array")
    t = -time()
    distance: List[List[float]] = []
    for x in range(image.width):
        row = []
        for y in range(image.height):
            if depths[x + y * image.height] > 0:
                row.append(0)
            else:
                row.append(100)
        distance.append(row)
    logging.debug(f"Finished in {t+time():.3} sec.")

    def transfer_value(x: int, y: int, dx: int, dy: int) -> float:
        if x + dx < 0 or x + dx >= image.height or y + dy < 0 or y + dy >= image.height:
            return 100

        horizontal = abs(dx) + abs(dy)
        if horizontal == 2:
            horizontal = 1.41

        za = heightmap.get(x, y)
        zb = heightmap.get(x + dx, y + dy)
        vertical = abs(za - zb) * 4
        return distance[x + dx][y + dy] + horizontal + vertical

    BAR_LENGHT = 60
    full_progress = 16 * image.width
    step = max((full_progress // BAR_LENGHT), 1)
    current_progress = 0

    logging.debug("Process irrigation distances")
    t = -time()
    for i in range(16):
        for x in range(image.width):
            for y in range(image.height):
                min_distance = distance[x][y]
                for dx in [-1, 0, 1]:
                    for dy in [-1, 0, 1]:
                        min_distance = min(min_distance, transfer_value(x, y, dx, dy))
                distance[x][y] = min_distance
            if logging.root.level <= logging.INFO:
                current_progress += 1
                progress_steps = current_progress // step
                print(f"\r[{'='*progress_steps:<{BAR_LENGHT}}]", end=' ')
    if logging.root.level <= logging.INFO:
        print()  # escape progress bar
    logging.debug(f"Finished in {t+time():.3} sec.")

    t = -time()
    moisture = []
    for x in range(image.width):
        for y in range(image.height):
            moisture.append(max(16 - distance[y][x], 0))

    return WaterMap(depths, moisture, image.size[0], image.size[1])
