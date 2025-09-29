import asyncio
from collections.abc import AsyncGenerator

import pymupdf
from pymupdf import Pixmap

from nebraska_pipeline.abstract_factory import Converter
from nebraska_pipeline.utils.constants import Constants

image_format: str = "jpeg"


class PDFToImageConverterPyMuPDF(Converter):
    def __init__(self, file_data: bytes, file_name: str, stream: bool = True):
        self.file_data: bytes = file_data
        self.file_name: str = file_name
        self.stream: bool = stream
        super().__init__()

    def _asynco_convert(
        self,
    ) -> list[bytes]:
        pages_data_in_bytes: list[bytes] = list()
        with pymupdf.open(stream=self.file_data) as pdf_file:
            for page in pdf_file:
                pages_as_img: Pixmap = page.get_pixmap(
                    matrix=Constants().returnPyMuPDFMatrix()
                )
                pages_data_in_bytes.append(pages_as_img.tobytes(output=image_format))

        return pages_data_in_bytes

    async def _stream_convert(
        self,
    ) -> AsyncGenerator[bytes, None]:
        matrix = Constants().returnPyMuPDFMatrix()
        with pymupdf.open(stream=self.file_data) as pdf_file:
            async for page in pdf_file:
                pages_as_img: Pixmap = page.get_pixmap(matrix=matrix)
                yield pages_as_img.tobytes(output=image_format)

    async def convert(self) -> list[bytes] | AsyncGenerator[bytes, None]:
        if self.stream:
            return self._stream_convert()
        else:
            return await asyncio.to_thread(self._asynco_convert)
