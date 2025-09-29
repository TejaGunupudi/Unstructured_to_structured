import time

from nebraska_pipeline import settings
from nebraska_pipeline.controller.helpers import (
    PreProcessingHelpers,
    ProcessingPiplineHelperMethods,
)
from nebraska_pipeline.temp_functions.post_processing import (
    additionalInformationCheck,
    applicationProcedureCheck,
    checkSuperVisionForDict,
    generalInformationextraction,
    generalInformationPositionCheck,
    generalPhysicalActivitiesCheck,
    liftHandlingConfidence,
    liftingHandlingreqs,
    liftinghandlingrerun,
    manualDexteritycheck,
    positionSummaryConfidenceCheck,
    responseFloatCheck,
    specificPhysicalreqshandling,
    supervisionCheck,
    zonedefinitionfactorConfidenceCheck,
    zoneDefinitionFactorsCheck,
)
from nebraska_pipeline.utils import PromptBuilder
from nebraska_pipeline.utils.app_logs import log_handler
from nebraska_pipeline.utils.enums import (
    LLMModelEnum,
    WordsMissingEnum,
)
from nebraska_pipeline.utils.patterns import (
    Patterns,
)


class FileProcessingPipelineController:
    async def processFile(self, file_data: bytes, file_name: str) -> tuple[dict, dict]:
        log_handler.info(f"file processing started for file : {file_name}")
        start_time = time.time()

        images_converted: list[
            bytes
        ] = await ProcessingPiplineHelperMethods.convertFileToImages(
            file_data=file_data, file_name=file_name
        )

        log_handler.info(
            f"Time taken for extracting images: {time.time() - start_time}"
        )

        images_to_str_converted_data: list[
            str
        ] = await ProcessingPiplineHelperMethods.convertImagesToStr(
            images=images_converted
        )

        log_handler.info(f"Time taken for extracting text: {time.time() - start_time}")

        text_from_images: str = "\n".join(images_to_str_converted_data)

        valid_template: bool = await PreProcessingHelpers.validateTemplate(
            text=text_from_images
        )
        if valid_template is False:
            raise ValueError(
                "[Error] : NotValidTemplateError, [reason] : Job Description File Is Not According To Template"
            )

        extracted_test_from_str: str = (
            await ProcessingPiplineHelperMethods.searchTextUsingPattern(
                patterns=[
                    Patterns.PATTERN,
                    Patterns.GENERAL_PHYSICAL_ACTIVITY_PATTERN_V2,
                ],
                text=text_from_images,
            )
        )

        extracted_attendance_from_str: str = (
            await ProcessingPiplineHelperMethods.searchTextUsingPattern(
                patterns=[
                    Patterns.ATTENDANCE_PATTERN,
                    Patterns.ATTENDANCE_PATTERN_V2,
                ],
                text=text_from_images,
            )
        )

        if extracted_test_from_str:
            general_physical_req_prompt_llm_output: str = (
                await ProcessingPiplineHelperMethods.askLLM(
                    prompt=PromptBuilder().constructActiveHrsExtractionPrompt(
                        extracted_text_general_physical_activity=extracted_test_from_str
                    ),
                    temperature=settings.MODEL_TEMPERATURE,
                    model=settings.MODEL_4O_MINI,
                )
            )
            general_physical_req_prompt: str = f"which I already calculated from here: {general_physical_req_prompt_llm_output}"
            log_handler.info("processing general physical req")

        else:
            general_physical_req_prompt: str = PromptBuilder.GENERAL_PHYSICAL_REQ_PROMPT
            log_handler.info("not processing general physical req")

        if extracted_attendance_from_str:
            attendance_req_prompt_llm_output: str = (
                await ProcessingPiplineHelperMethods.askLLM(
                    prompt=PromptBuilder().constructAttendancePrompt(
                        extracted_text_attendance_req=extracted_attendance_from_str
                    ),
                    temperature=settings.MODEL_TEMPERATURE,
                    model=settings.MODEL_4O_MINI,
                )
            )
            attendance_req_prompt: str = f"The attendance details extracted are: {attendance_req_prompt_llm_output}"
            log_handler.info("processing attendance req")

        else:
            attendance_req_prompt: str = PromptBuilder.GENERAL_PHYSICAL_REQ_PROMPT
            log_handler.info("not processing attendance req")

        markdown_response: str = await ProcessingPiplineHelperMethods.askLLM(
            prompt=PromptBuilder().constructMarkdownPrompt(
                general_physical_req_prompt=general_physical_req_prompt,
                attendance_req_prompt=attendance_req_prompt,
                file_name=file_name,
            ),
            temperature=settings.MODEL_TEMPERATURE,
            model=LLMModelEnum.MODEL_4O.value,
            images=images_converted,
        )
        if (
            WordsMissingEnum.KEYBOARDING.value not in markdown_response
            and WordsMissingEnum.FILING.value not in markdown_response
        ):
            markdown_response = (
                f"{markdown_response} \n {PromptBuilder.KEYBOARD_SUFFIX_STRING}"
            )

        json_response: str = await ProcessingPiplineHelperMethods.askLLM(
            prompt=PromptBuilder().constructJsonConversionPrompt(
                markdown_response=markdown_response
            ),
            temperature=settings.MODEL_TEMPERATURE,
            model=LLMModelEnum.MODEL_4O_MINI.value,
        )
        json_data = await ProcessingPiplineHelperMethods.extractJsonDataFromLLMResponse(
            json_response=json_response
        )
        try:
            if "zone definition factors" in text_from_images.lower():
                blank_descriptions = sum(
                    1
                    for factor in json_data.get("zone_definition_factors", [])
                    if not factor.get("description")
                )
                if blank_descriptions > 2:
                    markdown_response: str = (
                        await ProcessingPiplineHelperMethods.askLLM(
                            prompt=PromptBuilder().constructMarkdownPrompt(
                                general_physical_req_prompt=general_physical_req_prompt,
                                attendance_req_prompt=attendance_req_prompt,
                                file_name=file_name,
                            ),
                            temperature=settings.MODEL_TEMPERATURE,
                            model=LLMModelEnum.MODEL_4O.value,
                            images=images_converted,
                        )
                    )
                    if (
                        WordsMissingEnum.KEYBOARDING.value not in markdown_response
                        and WordsMissingEnum.FILING.value not in markdown_response
                    ):
                        markdown_response = f"{markdown_response} \n {PromptBuilder.KEYBOARD_SUFFIX_STRING}"
                    json_response: str = await ProcessingPiplineHelperMethods.askLLM(
                        prompt=PromptBuilder().constructJsonConversionPrompt(
                            markdown_response=markdown_response
                        ),
                        temperature=settings.MODEL_TEMPERATURE,
                        model=LLMModelEnum.MODEL_4O_MINI.value,
                    )
                    json_data = await ProcessingPiplineHelperMethods.extractJsonDataFromLLMResponse(
                        json_response=json_response
                    )
        except Exception:
            pass
        json_data = responseFloatCheck(json_data)
        json_data = applicationProcedureCheck(json_data, text_from_images)
        json_data = additionalInformationCheck(json_data, text_from_images)
        # json_data = await qualificationAttributesCheck(json_data, markdown_response)
        json_data = await supervisionCheck(json_data, text_from_images)
        json_data = await specificPhysicalreqshandling(json_data, text_from_images)
        json_data = zoneDefinitionFactorsCheck(
            json_data, text_from_images, markdown_response
        )
        json_data = await manualDexteritycheck(
            json_data, text_from_images=text_from_images
        )
        json_data = await liftinghandlingrerun(
            json_data,
            images_to_str_converted_data=images_to_str_converted_data,
            images_converted=images_converted,
            text_from_images=text_from_images,
        )
        json_data = liftingHandlingreqs(json_data)
        json_data = generalPhysicalActivitiesCheck(json_data)
        # confidence checks
        json_data = positionSummaryConfidenceCheck(json_data, text_from_images)
        json_data = zonedefinitionfactorConfidenceCheck(json_data, text_from_images)
        json_data = await generalInformationextraction(
            json_data=json_data, images_converted=images_converted
        )
        json_data = generalInformationPositionCheck(json_data)
        json_data = liftHandlingConfidence(json_data=json_data)
        json_data = checkSuperVisionForDict(json_data=json_data)
        confidence_score: dict = json_data.pop("confidence_scores")

        log_handler.info(f"Total time taken: {time.time() - start_time}")

        return confidence_score, json_data
