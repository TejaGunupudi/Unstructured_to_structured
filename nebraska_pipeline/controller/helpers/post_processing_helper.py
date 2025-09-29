import json

from nebraska_pipeline.controller.helpers.extract_text_helper import ExtractTextHelper
from nebraska_pipeline.controller.helpers.pipeline_helper import (
    ProcessingPiplineHelperMethods,
)
from nebraska_pipeline.utils.constants import Constants
from nebraska_pipeline.utils.enums import (
    JsonDataKeyEnum,
    LLMModelEnum,
    PhysicalActivitesTypeEnum,
    SpecificPhysicalRequirementsActivityEnum,
)
from nebraska_pipeline.utils.patterns import Patterns
from nebraska_pipeline.utils.prompts import PromptBuilder


class PostProcessingConfidenceCheck:
    @classmethod
    async def checkFloatValues(cls, confidence_score: dict) -> dict:
        for key, value in confidence_score.items():
            if isinstance(value, (float, str, int)):
                try:
                    confidence_score[key] = float(value)
                except Exception:
                    confidence_score[key] = 0.95
            elif isinstance(value, dict):
                cls.checkFloatValues(confidence_score=value)

    @classmethod
    async def applicationProcedureCheck(
        cls, confidence_score: dict, text_from_images: str
    ) -> dict:
        if confidence_score.get(JsonDataKeyEnum.APPLICATION_PROCEDURE) < 0.95:
            if "application procedure" not in text_from_images.lower():
                confidence_score[JsonDataKeyEnum.APPLICATION_PROCEDURE] = 0.95
        return confidence_score

    @classmethod
    async def additionalInformationCheck(
        cls, confidence_score: dict, text_from_images: str
    ) -> dict:
        if confidence_score.get(JsonDataKeyEnum.ADDITIONAL_INFORMATION) < 0.95:
            if "additional information" not in text_from_images.lower():
                confidence_score[JsonDataKeyEnum.ADDITIONAL_INFORMATION] = 0.95
        return confidence_score

    @classmethod
    async def qualificationAttributesCheck(
        cls,
        confidence_score: dict,
        markdown_response: str,
    ) -> tuple[dict, dict[str, list[str]] | None]:
        def _extractJsonData(json_string) -> dict | None:
            try:
                return json.loads(s=json_string)
            except Exception:
                return None

        qualification_json: dict[str, list[str]] | None = None
        if confidence_score.get(JsonDataKeyEnum.QUALIFICATIONS_AND_ATTRIBUTES) < 0.95:
            if "qualifications" in markdown_response.lower():
                qualifications_lines = (
                    await ExtractTextHelper.extractQualificationsSection(
                        text=markdown_response.lower(), keyword="qualifications"
                    )
                )
                if qualifications_lines:
                    qualification_string_response: str = (
                        await ProcessingPiplineHelperMethods.askLLM(
                            prompt=PromptBuilder.constructQualifactionPrompt(
                                qualifications_lines=qualifications_lines
                            ),
                            model=LLMModelEnum.MODEL_4O_MINI,
                        )
                    )
                    qualification_json_string: (
                        str | None
                    ) = await ProcessingPiplineHelperMethods.extractSpecificSection(
                        text=qualification_string_response,
                        pattern=Patterns.EXTRACT_JSON_RESPONCE_GREEDY,
                        group=0,
                    )
                    if qualification_json_string:
                        qualification_json = _extractJsonData(
                            json_string=qualification_json_string
                        )
                    else:
                        qualification_json = None
        if qualification_json:
            confidence_score[JsonDataKeyEnum.QUALIFICATIONS_AND_ATTRIBUTES] = 0.95
        return confidence_score, qualification_json

    @classmethod
    async def supervisionCheck(
        cls,
        confidence_score: dict[str, float | str | dict[str, float | str]],
        text_from_images: str,
        supervision_llm_output: str,
    ):
        if confidence_score.get(JsonDataKeyEnum.SUPERVISION) < 0.95:
            supervision_lines: str = (
                await ExtractTextHelper.extractLinesAfterSupervision(
                    text=text_from_images, lines_to_extract=4
                )
            )
            score: int = confidence_score.get(JsonDataKeyEnum.SUPERVISION)
            if (
                len(
                    set(supervision_llm_output.split()) & set(supervision_lines.split())
                )
                / len(set(supervision_llm_output.split()))
                >= 0.5
            ):
                score = 0.95

            confidence_score[JsonDataKeyEnum.SUPERVISION] = score

        return confidence_score

    @classmethod
    async def specificPhysicalReqshandlingCheck(
        cls,
        confidence_score: dict[str, float | str | dict[str, float | str]],
        text_from_images: str,
        physical_activities: dict[str, list[dict[str, str | list[dict]]]],
    ):
        physical_activities_score: dict = confidence_score.get(
            JsonDataKeyEnum.PHYSICAL_ACTIVITIES
        )
        reaching_overhead_empty: bool = False
        reaching_forward_occasional: bool = False
        reaching_low_occasional: bool = False
        overhead_line_has_other_data: bool = False
        if (
            physical_activities_score.get(
                PhysicalActivitesTypeEnum.SPECIFIC_PHYSICAL_REQS
            )
            < 0.95
        ):
            specific_physical_reqs_text_data: str | None = (
                ProcessingPiplineHelperMethods.searchTextUsingPattern(
                    patterns=[Patterns.SPECIFIC_PHYSICAL_REQS_TEXT_DATA_PATTERN],
                    text=text_from_images,
                    group=0,
                )
            )
            if specific_physical_reqs_text_data:
                for req in physical_activities.get(
                    PhysicalActivitesTypeEnum.SPECIFIC_PHYSICAL_REQS
                ):
                    if (
                        req.get("activity")
                        == SpecificPhysicalRequirementsActivityEnum.REACHING_OVERHEAD
                        and req.get("frequency") == ""
                    ):
                        reaching_overhead_empty = True
                    elif (
                        req["activity"]
                        == SpecificPhysicalRequirementsActivityEnum.REACHING_FORWARD
                        and "occas" in req.get("frequency").lower()
                    ):
                        reaching_forward_occasional = True
                    elif (
                        req.get("activity")
                        == SpecificPhysicalRequirementsActivityEnum.REACHING_LOW
                        and "occas" in req.get("frequency").lower()
                    ):
                        reaching_low_occasional = True

                overhead_lines: str | None = (
                    ProcessingPiplineHelperMethods.extractSpecificSection(
                        text=specific_physical_reqs_text_data.lower(),
                        pattern=Patterns.OVERHEAD,
                        group=0,
                    )
                )
                if overhead_lines:
                    if "overhead" in overhead_lines and len(overhead_lines.split()) > 1:
                        overhead_line_has_other_data = True
            if (
                reaching_overhead_empty
                and reaching_forward_occasional
                and reaching_low_occasional
                and overhead_line_has_other_data
            ):
                for req in physical_activities.get(
                    PhysicalActivitesTypeEnum.SPECIFIC_PHYSICAL_REQS
                ):
                    if (
                        req.get("activity")
                        == SpecificPhysicalRequirementsActivityEnum.REACHING_OVERHEAD
                    ):
                        req["frequency"] = "occasionally"
                        break

                confidence_score["physical_activities"]["specific_physical_reqs"] = 0.95

            special_physical_reqs: list[dict[str, str]] = physical_activities.get(
                PhysicalActivitesTypeEnum.SPECIFIC_PHYSICAL_REQS
            )
            for req in special_physical_reqs:
                if (
                    req.get("frequency")
                    and "occasional" in req.get("frequency").lower()
                ):
                    req["frequency"] = "occasionally"
                if (
                    req.get("frequency")
                    and "not applicable" in req.get("frequency").lower()
                ):
                    req["frequency"] = ""

            count_specific_physical_reqs = len(special_physical_reqs)

            if count_specific_physical_reqs < 16:
                existing_activities = {req["activity"] for req in special_physical_reqs}

                for activity in Constants.specificPhysicalReqRequiredKeywords():
                    if activity not in existing_activities:
                        special_physical_reqs.append(
                            {"activity": activity, "frequency": ""}
                        )

            physical_activities["specific_physical_reqs"] = special_physical_reqs

        return physical_activities
