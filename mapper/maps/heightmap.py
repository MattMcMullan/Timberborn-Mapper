#  _  _     _      _   _
# | || |___(_)__ _| |_| |_ _ __  __ _ _ __
# | __ / -_) / _` | ' \  _| '  \/ _` | '_ \
# |_||_\___|_\__, |_||_\__|_|_|_\__,_| .__/
#            |___/                   |_|
# Heightmap
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple, Union, Any

from image_utils import MapImage
from maps.format import TimberbornArray, TimberbornMapSize, TimberbornSize, TimberbornTerrainMap


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
        assert x < self.width
        assert y < self.height
        return self.data[x + y * self.width]


@dataclass
class ImageToTimberbornHeightmapLinearConversionSpec:
    min_height: int = 3
    max_height: int = 16


@dataclass
class ImageToTimberbornHeightmapBucketizedConversionSpec:
    weights: List[float] = field(
        default_factory=lambda: [
            0.0,
            0.0,
            0.067,
            0.1,
            0.11,
            0.14,
            0.15,
            0.07,
            0.13,
            0.079,
            0.049,
            0.022,
            0.022,
            0.011,
            0.018,
            0.017,
        ]
    )


@dataclass
class ImageToTimberbornHeightmapSpec:
    def __init__(
        self,
        filename: str,
        linear_conversion: Union[Optional[ImageToTimberbornHeightmapLinearConversionSpec], dict] = None,
        bucketized_conversion: Union[Optional[ImageToTimberbornHeightmapBucketizedConversionSpec], dict] = None,
    ):
        self.filename = filename

        if isinstance(linear_conversion, dict):
            linear_conversion = ImageToTimberbornHeightmapLinearConversionSpec(**linear_conversion)
        self.linear_conversion = linear_conversion

        if isinstance(bucketized_conversion, dict):
            bucketized_conversion = ImageToTimberbornHeightmapBucketizedConversionSpec(**bucketized_conversion)
        self.bucketized_conversion = bucketized_conversion

        assert (
            self.linear_conversion is None or self.bucketized_conversion is None
        ), "Linear heightmap conversion and bucketized heightmap conversion are mutually exclusive"

        if self.linear_conversion is None and self.bucketized_conversion is None:
            self.linear_conversion = ImageToTimberbornHeightmapLinearConversionSpec()

    filename: str
    linear_conversion: Optional[ImageToTimberbornHeightmapLinearConversionSpec]
    bucketized_conversion: Optional[ImageToTimberbornHeightmapBucketizedConversionSpec]


def bucketize_data(data: List[float], bucket_weights: List[float]) -> List[int]:
    bucket_cutoffs = [
        math.ceil(sum(bucket_weights[:i]) / sum(bucket_weights) * len(data)) for i in range(1, len(bucket_weights) + 1)
    ]
    bucket_cutoffs[-1] += 1
    print(bucket_cutoffs)

    sortable: List[Tuple[int, float]] = [(i, v) for i, v in enumerate(data)]
    sortable.sort(key=lambda t: t[1])
    result = [0] * len(data)
    for i, s in enumerate(sortable):
        for bucket, cutoff in enumerate(bucket_cutoffs):
            if cutoff > i:
                result[s[0]] = bucket
                assert bucket < 16, f"{bucket} >= 16. 16 is the largest number of layers supported by Timberborn"
                break
        else:
            assert False, f"{i} pixel was missed."

    return result


def read_heightmap(width: int, height: int, path: Path, spec: ImageToTimberbornHeightmapSpec, args: Any) -> Heightmap:
    print("\nReading Heightmap")

    filepath = path / spec.filename

    map_image = MapImage(filepath, width, height)

    if spec.linear_conversion is not None:
        print("Converting image to heightmap data with method: linear")
        output_range = spec.linear_conversion.max_height - spec.linear_conversion.min_height
        height_data = []
        for pixel in map_image.normalized_data:
            height = round(pixel * output_range + spec.linear_conversion.min_height)
            height_data.append(height)
    elif spec.bucketized_conversion is not None:
        print("Converting image to heightmap data with method: bucketized")
        height_data = [b for b in bucketize_data(map_image.normalized_data, spec.bucketized_conversion.weights)]
    else:
        assert False, "Must specify a conversion method for heightmap data."

    return Heightmap(
        min_height=min(height_data),
        max_height=max(height_data),
        width=map_image.image.size[0],
        height=map_image.image.size[1],
        data=height_data,
    )
