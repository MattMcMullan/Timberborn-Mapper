#  ___                     _  _                    _ _         _   _
# |_ _|_ __  __ _ __ _ ___| \| |___ _ _ _ __  __ _| (_)_____ _| |_(_)___ _ _
# | || '  \/ _` / _` / -_) .` / _ \ '_| '  \/ _` | | |_ / _` |  _| / _ \ ' \
# |___|_|_|_\__,_\__, \___|_|\_\___/_| |_|_|_\__,_|_|_/__\__,_|\__|_\___/_||_|
#               |___/
# Image Normalization
import logging
from pathlib import Path
from typing import List

from PIL import Image, ImageOps


def read_monochrome_image(filename: Path, width: int, height: int) -> Image.Image:
    image = Image.open(filename)

    try:
        image.verify()
    except Exception as exc:
        logging.critical("Couldn't verify '%s' as image file, it might be broken or not an image.", filename)
        raise exc
    image = Image.open(filename)  # it has to be re-opened after verify()

    image = ImageOps.mirror(image)  # Timberborn's map array structures are mirrored horizontally:
    logging.info(f"Image Size: {image.size}")

    image = image.convert("I")
    if width > 0:
        logging.info(f"Adjusting width to {width}")
        image = image.resize((width, image.height))

    if height > 0:
        logging.info(f"Adjusting height to {height}")
        image = image.resize((image.width, height))

    return image


class MapImage:
    image = None
    _normalized_data = None
    _rounded_normalized_data = None

    def __init__(self, filename: Path, width: int, height: int):
        self.image = read_monochrome_image(filename, width, height)

    @property
    def normalized_data(self) -> List[float]:
        if not self._normalized_data:
            self._normalized_data = self.normalize_image_data()
        return self._normalized_data

    @property
    def rounded_normalized_data(self) -> List[int]:
        if not self._rounded_normalized_data:
            self._rounded_normalized_data = [round(pixel) for pixel in self.normalized_data]
        return self._rounded_normalized_data

    def normalize_image_data(self) -> List[float]:
        data = self.image.getdata()
        image_min = min(data)
        image_max = max(data)
        image_range = image_max - image_min
        print(f"Image Data Range: {image_min} - {image_max}")

        return [(pixel - image_min) / image_range for pixel in data]
