import asyncio
import json
import os
import re

from openai import AsyncAzureOpenAI
from pydantic import BaseModel

from nebraska_pipeline import settings
from nebraska_pipeline.core.v1.converter import (
    DocToPDF,
    ImageToStrOCRPyTesseract,
    PDFToImageConverterPyMuPDF,
)
from nebraska_pipeline.core.v1.llm import AzureOpenAILLM
from nebraska_pipeline.storage import (  # noqa: F401  # noqa: F401
    azure_service_bus_client,
    storage,
)
from nebraska_pipeline.utils.app_logs import log_handler
from nebraska_pipeline.utils.enums import (
    LLMModelEnum,
)
from nebraska_pipeline.utils.exceptions import FileNotSupportedError
from nebraska_pipeline.utils.patterns import (
    Patterns,
)


class FileProcessingPiplineHelper:
    @classmethod
    async def tokenLoger(cls, model: str, input_token: int, output_token: int) -> None:
        log_handler.info(
            msg=f"Tokens used for model : {model} | input_token : {input_token} | output_token : {output_token}"
        )

    @classmethod
    async def splitFilenName(cls, file_name: str) -> tuple[str, str]:
        return os.path.splitext(file_name)

    @classmethod
    async def extractSpecificSection(
        cls,
        text: str,
        pattern: str,
        group: int = 1,
        flags=re.DOTALL,
    ) -> str | None:
        match = re.search(pattern=pattern, string=text, flags=flags)
        return match.group(group).strip() if match else None

    @classmethod
    async def extractJsonDataFromLLMResponse(cls, json_response: str) -> dict:
        return json.loads(
            re.search(
                Patterns.JSON_EXTRACT_FROM_LLM_RESPOSNE_PATTERN,
                json_response,
                re.DOTALL,
            ).group(0)
        )

    @classmethod
    async def convertFileToImages(cls, file_data: bytes, file_name: str) -> list[bytes]:
        async def _convertPdfToImages(
            file_in_bytes: bytes, file_name_with_ext: str
        ) -> list[bytes]:
            return await PDFToImageConverterPyMuPDF(
                file_data=file_in_bytes,
                file_name=file_name_with_ext,
                stream=False,
            ).convert()

        _, file_type = await cls.splitFilenName(file_name=file_name)
        if file_type in [".pdf", "pdf"]:
            return await _convertPdfToImages(
                file_in_bytes=file_data,
                file_name_with_ext=file_name,
            )

        if file_type in ["doc", "docx", ".doc", ".docx"]:
            file_data_converted, file_name_converted = await DocToPDF(
                doc_file_in_byte=file_data, file_name=file_name
            ).convert()
            return await _convertPdfToImages(
                file_in_bytes=file_data_converted,
                file_name_with_ext=file_name_converted,
            )

        raise FileNotSupportedError

    @classmethod
    async def convertImagesToStr(cls, images: list[bytes]) -> list[str]:
        return await asyncio.gather(
            *[ImageToStrOCRPyTesseract(images=image).convert() for image in images]
        )

    @classmethod
    async def searchTextUsingPattern(
        cls, patterns: list[str], text: str, group: int = 1
    ) -> str:
        extracted_text: str
        for pattern in patterns:
            extracted_text = await cls.extractSpecificSection(
                text=text, pattern=pattern, group=group
            )
            if extracted_text:
                break
        return extracted_text

    @classmethod
    async def checkWordsExist(cls, keywords: list[str], text: str):
        return [keyword.lower() in text for keyword in keywords]

    @classmethod
    async def askLLM(
        cls,
        prompt: str,
        images: list[bytes] | None = None,
        temperature: float = settings.MODEL_TEMPERATURE,
        model: LLMModelEnum = LLMModelEnum.MODEL_4O_MINI.value,
        pydantic_model: BaseModel | None = None,
    ):
        azure_llm_instance: AzureOpenAILLM = AzureOpenAILLM(
            azure_opean_ai_client=AsyncAzureOpenAI(
                azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
                api_key=settings.AZURE_OPENAI_KEY,
                api_version=settings.AZURE_OPENAI_API_VERSION,
            ),
            prompt=prompt,
            images=images,
            temperature=temperature,
            model=model,
            pydantic_model=pydantic_model,
        )
        if images:
            output, in_token, out_token = await azure_llm_instance.askWithImage()
            await cls.tokenLoger(
                model=model,
                input_token=in_token,
                output_token=out_token,
            )
            return output
        elif pydantic_model is None:
            output, in_token, out_token = await azure_llm_instance.ask()
            await cls.tokenLoger(
                model=model,
                input_token=in_token,
                output_token=out_token,
            )
            return output
        else:
            (
                output,
                in_token,
                out_token,
            ) = await azure_llm_instance.askWithStructuredResposne()
