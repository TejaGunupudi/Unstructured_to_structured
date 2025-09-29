import asyncio
from concurrent.futures import ProcessPoolExecutor, as_completed

import cv2
import numpy
import PIL
import PIL.Image
import pytesseract

from nebraska_pipeline.abstract_factory import Converter
from nebraska_pipeline.utils.constants import Constants


class ImageToStrOCRPyTesseract(Converter):
    def __init__(self, images: list[bytes] | bytes, multi_processing: bool = False):
        self.images: list[bytes] | bytes = images
        self.multi_processing: bool = multi_processing
        super().__init__()

    def _convert(self, image: bytes) -> str:
        nparry_of_image = numpy.frombuffer(image, numpy.uint8)
        cv2_image = cv2.imdecode(nparry_of_image, cv2.IMREAD_COLOR)
        cv2_resized_image = cv2.resize(
            src=cv2_image,
            dsize=None,
            fx=Constants.FX,
            fy=Constants.FY,
            interpolation=cv2.INTER_LINEAR,
        )
        cv2_gray_image = cv2.cvtColor(src=cv2_resized_image, code=cv2.COLOR_BGR2GRAY)
        cv2_threshold_image = cv2.adaptiveThreshold(
            src=cv2_gray_image,
            maxValue=Constants.ADAPTIVE_THRESHOLD_MAXVALUE,
            adaptiveMethod=cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            thresholdType=cv2.THRESH_BINARY,
            blockSize=Constants.BLOCK_SIZE,
            C=Constants.ADAPTIVE_THRESHOLD_C_VALUE,
        )
        cv2_thresholded_image = cv2.fastNlMeansDenoising(
            src=cv2_threshold_image,
            h=Constants.FAST_NL_MEANS_H_VALUE,
            templateWindowSize=Constants.TEMPLATE_WINDOW_SIZE,
            searchWindowSize=Constants.SEARCH_WINDOW_SIZE,
        )
        del (
            nparry_of_image,
            cv2_image,
            cv2_resized_image,
            cv2_gray_image,
            cv2_threshold_image,
        )
        return pytesseract.image_to_string(PIL.Image.fromarray(cv2_thresholded_image))

    async def convert(self) -> list[str] | str:
        if isinstance(self.images, list):
            if self.multi_processing:
                with ProcessPoolExecutor() as executor:
                    futures: list = [
                        executor.submit(self._convert, image) for image in self.images
                    ]
                return [future.result() for future in as_completed(futures)]
            else:
                return [
                    await asyncio.to_thread(self._convert, image)
                    for image in self.images
                ]
        if isinstance(self.images, bytes):
            return self._convert(image=self.images)
        raise ValueError(
            f"input should be type list[bytes] or bytes but got {type(self.images)}"
        )
