import os
import tempfile

import doc2pdf

from nebraska_pipeline.abstract_factory import Converter
from nebraska_pipeline.utils.app_logs import log_handler


class DocToPDF(Converter):
    def __init__(self, doc_file_in_byte: bytes, file_name: str):
        self.doc_file_in_byte: bytes = doc_file_in_byte
        self.file_name: bytes = file_name
        super().__init__()

    async def convert(self) -> tuple[bytes, str]:
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=f".{self.file_name.split('.')[-1]}",
        ) as temp_documnet:
            temp_documnet.write(self.doc_file_in_byte)
            temp_document_path = temp_documnet.name

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
            temp_pdf_path = temp_pdf.name

        try:
            doc2pdf.convert(in_file=temp_document_path, out_file=temp_pdf_path)

            with open(temp_pdf_path, "rb") as pdf_file:
                pdf_bytes: bytes = pdf_file.read()

        finally:
            os.remove(temp_document_path)
            os.remove(temp_pdf_path)

        log_handler.info("converted to pdf")
        return pdf_bytes, temp_pdf_path
