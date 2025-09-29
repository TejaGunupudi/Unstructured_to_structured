import asyncio
import base64

from openai import AsyncAzureOpenAI
from pydantic import BaseModel

from nebraska_pipeline.abstract_factory import LLM
from nebraska_pipeline.utils.enums import LLMModelEnum


class AzureOpenAILLM(LLM):
    def __init__(
        self,
        azure_opean_ai_client: AsyncAzureOpenAI,
        prompt: str,
        temperature: str,
        model: LLMModelEnum,
        images: list[bytes] | None = None,
        pydantic_model: BaseModel | None = None,
    ):
        self.azure_opean_ai_client: AsyncAzureOpenAI = azure_opean_ai_client
        self.prompt: str = prompt
        self.temperature: str = temperature
        self.model: LLMModelEnum = model
        self.images: list[bytes] | None = images
        self.pydantic_model: BaseModel = pydantic_model
        super().__init__()

    def _returnMimeType(self, file_type: str, file_ext: str):
        return f"{file_type}/{file_ext}"  # image/jpeg for jpeg

    async def _convertBytesToBase64(self, i: bytes):
        base64_encoded_data = base64.b64encode(i).decode("utf-8")
        return f"data:{self._returnMimeType(file_type='image', file_ext='jpeg')};base64,{base64_encoded_data}"

    async def _convertImageToLLMUnderstandableURL(self, image: bytes):
        return {
            "type": "image_url",
            "image_url": {"url": await self._convertBytesToBase64(i=image)},
        }

    async def ask(self):
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": self.prompt},
        ]

        response = await self.azure_opean_ai_client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
        )

        return (
            response.choices[0].message.content,
            response.usage.prompt_tokens,
            response.usage.completion_tokens,
        )

    async def askWithImage(self):
        content: list[dict] = [{"type": "text", "text": self.prompt}]
        content.extend(
            await asyncio.gather(
                *[
                    self._convertImageToLLMUnderstandableURL(image=image)
                    for image in self.images
                ]
            )
        )

        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {
                "role": "user",
                "content": content,
            },
        ]

        response = await self.azure_opean_ai_client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
        )
        del content

        return (
            response.choices[0].message.content,
            response.usage.prompt_tokens,
            response.usage.completion_tokens,
        )

    async def askWithStructuredResposne(self):
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": self.prompt},
        ]

        response = await self.azure_opean_ai_client.beta.chat.completions.parse(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            response_format=self.pydantic_model,
        )

        return (
            response.model_dump(),
            response.usage.prompt_tokens,
            response.usage.completion_tokens,
        )
