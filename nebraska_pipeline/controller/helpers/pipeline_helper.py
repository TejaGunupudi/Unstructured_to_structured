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
from nebraska_pipeline.utils.app_logs import log_handler
from nebraska_pipeline.utils.enums import (
    ConfidenceEnum,
    LLMModelEnum,
)
from nebraska_pipeline.utils.exceptions import FileNotSupportedError
from nebraska_pipeline.utils.patterns import (
    Patterns,
)


class ProcessingPiplineHelperMethods:
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
        if file_type.lower() in [".pdf", "pdf"]:
            return await _convertPdfToImages(
                file_in_bytes=file_data,
                file_name_with_ext=file_name,
            )

        if file_type.lower() in ["doc", "docx", ".doc", ".docx"]:
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

    @classmethod
    def checkIfJsonIsReadyForExport(
        cls, report: dict[str, float | str | dict[str, float | str]]
    ) -> bool:
        for key, value in report.items():
            if isinstance(value, (float, str, int)):
                try:
                    if float(value) < 0.85:
                        return False
                except Exception:
                    pass
            if isinstance(value, dict):
                if not cls.checkIfJsonIsReadyForExport(report=value):
                    return False
        return True

    @classmethod
    async def overalConfidence(
        cls,
        confidence_score: dict[str, float | dict[str, float]],
    ) -> ConfidenceEnum:
        confidence_list: list[ConfidenceEnum] = []

        def _calculateConfidence(score: dict[str, float | dict[str, float]]):
            for key, value in score.items():
                if isinstance(value, (float, str, int)):
                    if float(value) < 0.85:
                        confidence_list.append(ConfidenceEnum.LOW)
                    if float(value) < 0.95 and float(value) >= 0.85:
                        confidence_list.append(ConfidenceEnum.MEDIUM)
                    elif float(value) >= 0.95:
                        confidence_list.append(ConfidenceEnum.HIGH)
                if isinstance(value, dict):
                    _calculateConfidence(score=value)

        _calculateConfidence(score=confidence_score)
        if confidence_score.get("general_information") < 0.85:
            return ConfidenceEnum.LOW
        if confidence_score.get("general_information") >= 0.85:
            if confidence_list.count(ConfidenceEnum.LOW) <= 2:
                return ConfidenceEnum.MEDIUM
            else:
                return ConfidenceEnum.LOW
        if confidence_list.count(ConfidenceEnum.LOW) > 0:
            return ConfidenceEnum.LOW
        if confidence_list.count(ConfidenceEnum.MEDIUM) > 5:
            return ConfidenceEnum.MEDIUM
        return ConfidenceEnum.HIGH
