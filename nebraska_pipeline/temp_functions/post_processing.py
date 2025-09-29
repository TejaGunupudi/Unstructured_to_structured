import ast
import re

from nebraska_pipeline import settings
from nebraska_pipeline.controller.helpers.extract_text_helper import ExtractTextHelper
from nebraska_pipeline.utils.enums import (
    LLMModelEnum,
)
from nebraska_pipeline.utils.prompts import PromptBuilder
from nebraska_pipeline.utils.static import staticLiftHandling
from nebraska_pipeline.utils.utilities import (
    extract_general_information,
    retry,
)

from .temp_pipeline import FileProcessingPiplineHelper


def responseFloatCheck(json_data):
    def check_and_set_floats(conf_scores):
        for key, value in conf_scores.items():
            if isinstance(value, dict):
                check_and_set_floats(value)
            else:
                if isinstance(value, float):
                    continue
                try:
                    conf_scores[key] = float(value)
                except (ValueError, TypeError):
                    conf_scores[key] = 0.95
        return conf_scores

    if "confidence_scores" in json_data:
        json_data["confidence_scores"] = check_and_set_floats(
            json_data["confidence_scores"]
        )
    return json_data


def applicationProcedureCheck(json_data: dict, text_from_images: str) -> dict:
    if json_data["confidence_scores"]["application_procedure"] < 0.95:
        if "application procedure" not in text_from_images.lower():
            json_data["confidence_scores"]["application_procedure"] = 0.95
    return json_data


def additionalInformationCheck(json_data: dict, text_from_images: str) -> dict:
    if json_data["confidence_scores"]["additional_information"] < 0.95:
        if "additional information" not in text_from_images.lower():
            json_data["confidence_scores"]["additional_information"] = 0.95
    if json_data["additional_information"] == "":
        json_data["confidence_scores"]["additional_information"] = 0.95
    return json_data


def generalInformationPositionCheck(json_data: dict) -> dict:
    if json_data.get("general_information").get("position_number") in ["0", 0]:
        json_data["general_information"]["position_number"] = ""
    invalid_position_numbers = ["", 0, "0", "N/A"]

    if json_data["general_information"]["position_number"] in invalid_position_numbers:
        json_data["confidence_scores"]["general_information"] = 0.8

    if json_data["general_information"]["working_job_title"] == "":
        json_data["confidence_scores"]["general_information"] = 0.8

    return json_data

    # async def qualificationAttributesCheck(json_data: dict, markdown_response: str) -> dict:
    #     qualification_json: str | dict = ""
    #     if json_data["confidence_scores"]["qualifications_and_attributes"] < 0.95:
    #         if "qualifications" in markdown_response.lower():
    #             qualifications_lines = extract_qualifications_section(
    #                 text=markdown_response.lower(), keyword="qualifications"
    #             )
    #             if qualifications_lines:
    #                 qualification_prompt: str = f"""
    #     I want you to extract the qualifications specifics in the mentioned JSON format from the given data.
    #     Make sure to correctly classify the qualifications into the appropriate list in the JSON, based on the content provided.

    #     ### Rules:
    #     1. Any qualifications explicitly marked as "minimum qualifications" should go under "minimum_qualifications," even if they appear to be helpful or beneficial.
    #     2. If the qualifications are implied as required but not explicitly stated, place them under "required_qualifications".
    #     3. If the qualifications are preferred or considered a bonus, place them under "preferred_qualifications".
    #     4. Qualifications that could be helpful but are not explicitly required or preferred go under "helpful_qualifications".
    #     5. Any additional information that does not fit into the above categories goes under "other_information".

    #     ### Important:
    #     - All qualifications listed under a specific header, such as "minimum qualifications," must be fully included in the corresponding category in the JSON, even if they seem to fit other categories like helpful or preferred.
    #     - Do not split sentences from the same qualification header into different categories. this is very strict.

    #     Qualification JSON:
    #     {{
    #     "required_qualifications": [],
    #     "preferred_qualifications": [],
    #     "helpful_qualifications": [],
    #     "minimum_qualifications": [],
    #     "other_information": []
    #     }}

    #     Input data:
    #     {qualifications_lines}

    #     Your task is to parse the input data carefully and provide the output in the exact JSON format above. Make sure no qualifications are missed or misplaced, and all points under "minimum qualifications" go directly under "minimum_qualifications."
    #     """
    #                 qualification_json_string = await FileProcessingPiplineHelper.askLLM(
    #                     prompt=qualification_prompt, model=settings.MODEL_4O_MINI
    #                 )
    #                 qualification_json = extract_json_from_string(qualification_json_string)
    #             if qualification_json:
    #                 json_data["qualifications_and_attributes"] = qualification_json
    #                 json_data["confidence_scores"]["qualifications_and_attributes"] = 0.95

    def replace_empty_strings(item):
        if isinstance(item, dict):
            return {k: replace_empty_strings(v) for k, v in item.items()}
        elif isinstance(item, list):
            return [replace_empty_strings(element) for element in item]
        elif isinstance(item, str):
            return [] if item == "" else item
        else:
            return item

    json_data["qualifications_and_attributes"] = replace_empty_strings(
        json_data["qualifications_and_attributes"]
    )

    return json_data


async def supervisionCheck(json_data: dict, text_from_images: str) -> dict:
    supervision_received_count = text_from_images.count("supervision received")
    supervision_exercised_count = text_from_images.count("supervision exercised")
    if supervision_received_count >= 2 and supervision_exercised_count >= 2:
        json_data["confidence_scores"]["supervision"] = 0.90

    elif "supervision" not in text_from_images.lower():
        json_data["confidence_scores"]["supervision"] = 0.95

    elif json_data["confidence_scores"]["supervision"] < 0.95:
        supervision_lines = await ExtractTextHelper.extractLinesAfterSupervision(
            text_from_images, 4
        )
        supervision_text = str(json_data["supervision"])
        if supervision_text:
            json_data["confidence_scores"]["supervision"] = (
                0.95
                if (
                    len(set(supervision_text.split()) & set(supervision_lines.split()))
                    / len(set(supervision_text.split()))
                )
                >= 0.5
                else json_data["confidence_scores"]["supervision"]
            )
    return json_data


async def specificPhysicalreqshandling(json_data: dict, text_from_images: str) -> dict:
    specific_physical_reqs_text_data: str | None = None
    if (
        json_data["confidence_scores"]["physical_activities"]["specific_physical_reqs"]
        < 0.95
    ):
        specific_physical_reqs_text_data_pattern = (
            r"THIS JOB REQUIRES EMPLOYEE TO:.*?THIS JOB REQUIRES EMPLOYEE TO:"
        )
        specific_physical_reqs_text_data = (
            await FileProcessingPiplineHelper.searchTextUsingPattern(
                patterns=[specific_physical_reqs_text_data_pattern],
                text=text_from_images,
                group=0,
            )
        )

        if specific_physical_reqs_text_data is not None:
            specific_physical_reqs_text_data_lower = (
                specific_physical_reqs_text_data.lower()
            )

            # Initialize flags
            reaching_overhead_empty = False
            reaching_forward_occasional = False
            reaching_low_occasional = False
            overhead_line_has_other_data = False

            # Iterate through the list to check conditions
            for req in json_data["physical_activities"]["specific_physical_reqs"]:
                if req["activity"] == "reaching_overhead" and req["frequency"] == "":
                    reaching_overhead_empty = True
                elif (
                    req["activity"] == "reaching_forward"
                    and "occas" in req["frequency"].lower()
                ):
                    reaching_forward_occasional = True
                elif (
                    req["activity"] == "reaching_low"
                    and "occas" in req["frequency"].lower()
                ):
                    reaching_low_occasional = True

            # Check for the overhead keyword line with other data
            overhead_match = re.search(
                r"overhead.*", specific_physical_reqs_text_data_lower
            )
            if overhead_match:
                overhead_line = overhead_match.group(0)
                if "overhead" in overhead_line and len(overhead_line.split()) > 1:
                    overhead_line_has_other_data = True

            if (
                reaching_overhead_empty
                and reaching_forward_occasional
                and reaching_low_occasional
                and overhead_line_has_other_data
            ):
                for req in json_data["physical_activities"]["specific_physical_reqs"]:
                    if req["activity"] == "reaching_overhead":
                        req["frequency"] = "occasionally"
                        # json_data["physical_activities"][
                        #     "specific_physical_reqs"
                        # ] = specific_physical_reqs
                        break

                json_data["confidence_scores"]["physical_activities"][
                    "specific_physical_reqs"
                ] = 0.95

    for req in json_data["physical_activities"]["specific_physical_reqs"]:
        # Check if 'frequency' is present and not None
        if req.get("frequency") and "occasional" in req["frequency"].lower():
            req["frequency"] = "occasionally"
        if req.get("frequency") and "not applicable" in req["frequency"].lower():
            req["frequency"] = ""
    required_activities = [
        "squating",
        "bending",
        "kneeling",
        "reaching_overhead",
        "reaching_forward",
        "reaching_low",
        "twisting",
        "crawling",
        "climbing_ladders",
        "climbing_stairs",
        "climbing_other",
        "walking_on_rough_ground",
        "exposure_to_changes_of_temperature_humidity",
        "exposure_to_dust_fumes_gases_chemicals",
        "being_near_moving_machinery",
        "working_from_heights",
    ]
    count_specific_physical_reqs = len(
        json_data["physical_activities"]["specific_physical_reqs"]
    )

    if count_specific_physical_reqs < 16:
        existing_activities = {
            req["activity"]
            for req in json_data["physical_activities"]["specific_physical_reqs"]
        }

        for activity in required_activities:
            if activity not in existing_activities:
                json_data["physical_activities"]["specific_physical_reqs"].append(
                    {"activity": activity, "frequency": ""}
                )

    # json_data["physical_activities"]["specific_physical_reqs"] = json_data[
    #     "physical_activities"
    # ]["specific_physical_reqs"]
    return json_data


def zoneDefinitionFactorsCheck(
    json_data: dict, text_from_images: str, markdown_response: str
) -> dict:
    if json_data["confidence_scores"]["zone_definition_factors"] < 0.95:
        text_from_images_lower = text_from_images.lower()
        markdown_response_lower = markdown_response.lower()
        zone_definition_factor_list = [
            "nature/complexity of work",
            "problem solving/decision-making",
            "strategic impact",
            "know how",
            "technical know how",
            "interactions",
            "leadership",
        ]
        # remooving the element if there is no description
        for i, factor in enumerate(json_data["zone_definition_factors"]):
            if factor["description"] == "":
                factor_name = factor["factor"].lower()
                if factor_name in zone_definition_factor_list:
                    zone_definition_factor_list.remove(factor_name)

        # Check if all elements are present in both text_from_images_lower and markdown_response_lower
        all_present_in_images = all(
            factor in text_from_images_lower for factor in zone_definition_factor_list
        )
        all_present_in_markdown = all(
            factor in markdown_response_lower for factor in zone_definition_factor_list
        )

        if all_present_in_images and all_present_in_markdown:
            json_data["confidence_scores"]["zone_definition_factors"] = 0.95
    return json_data


async def manualDexteritycheck(json_data: dict, text_from_images: str) -> dict:
    async def dexterity_pattern_run():
        dexterity_text_data_pattern = r"POSITION REQUIRES USE OF HANDS OR SPECIAL TOOLS.*?POSITION REQUIRES ATTENDANCE AT THE WORKPLACE"
        dexterity_text_data_pattern_v2 = (
            r"POSITION REQUIRES USE OF HANDS OR SPECIAL TOOLS.*?THIS POSITION"
        )
        dexterity_text_data = await FileProcessingPiplineHelper.searchTextUsingPattern(
            patterns=[dexterity_text_data_pattern, dexterity_text_data_pattern_v2],
            text=text_from_images,
            group=0,
        )
        return dexterity_text_data

    dexterity_text_data = await dexterity_pattern_run()
    if (
        json_data["confidence_scores"]["physical_activities"]["manual_dexterity_reqs"]
        < 0.95
        or all(
            not value
            for value in json_data["physical_activities"]["manual_dexterity_reqs"][
                "keyboarding"
            ].values()
        )
        and all(
            not value
            for value in json_data["physical_activities"]["manual_dexterity_reqs"][
                "filing"
            ].values()
        )
    ):
        if (
            dexterity_text_data is not None
            and all(
                not value
                for value in json_data["physical_activities"]["manual_dexterity_reqs"][
                    "keyboarding"
                ].values()
            )
            and all(
                not value
                for value in json_data["physical_activities"]["manual_dexterity_reqs"][
                    "filing"
                ].values()
            )
        ):
            dexterity_text_data_lower = dexterity_text_data.lower()
            filing_updated = False
            keyboarding_updated = False
            # Check for "keyboarding" line
            keyboarding_match = re.search(r"keyboarding.*", dexterity_text_data_lower)
            if keyboarding_match:
                keyboarding_line = keyboarding_match.group(0)
                if (
                    "keyboarding" in keyboarding_line
                    and len(keyboarding_line.split()) > 1
                ):
                    json_data["physical_activities"]["manual_dexterity_reqs"][
                        "keyboarding"
                    ]["both_hands"] = True
                    keyboarding_updated = True

            # Check for "filing" line
            filing_match = re.search(r"filing.*", dexterity_text_data_lower)
            if filing_match:
                filing_line = filing_match.group(0)
                if "filing" in filing_line and len(filing_line.split()) > 1:
                    json_data["physical_activities"]["manual_dexterity_reqs"]["filing"][
                        "both_hands"
                    ] = True
                    filing_updated = True

            if keyboarding_updated and filing_updated:
                json_data["confidence_scores"]["physical_activities"][
                    "manual_dexterity_reqs"
                ] = 0.95
    if (
        json_data["physical_activities"]["manual_dexterity_reqs"]["other_description"]
        == ""
    ):
        if dexterity_text_data:
            if (
                "operation" in dexterity_text_data.lower()
                and "equipment" in dexterity_text_data.lower()
            ):
                json_data["physical_activities"]["manual_dexterity_reqs"][
                    "other_description"
                ] = "Operation of standard office equipment"
    # change the code  tilla bove only here the below is under experiment/////////////////////////////////////////
    # search_using_pattern = await self._searchTextUsingPattern(
    #     patterns=r"POSITION REQUIRES USE OF HANDS OR SPECIAL TOOLS.*?This position may be lower",
    #     text=text_from_images,
    # )
    # print(
    #     "search_using_pattern manual dexterity................",
    #     search_using_pattern,
    # )
    # if
    #     if search_using_pattern:
    #         search_string_identified =

    #     search_string = "POSITION REQUIRES USE OF HANDS OR SPECIAL TOOLS"
    #             found_index = -1
    #             for index, page_text in enumerate(images_to_str_converted_data):
    #                 if search_string in page_text:
    #                     found_index = index
    #                     break
    #             if found_index != -1:
    #                 print(
    #                     f"The string '{search_string}' is found on page/element {found_index + 1}"
    #                 )
    #                 dexerity_prompt = """
    # I am attaching an image data for you:
    # For tools (' POSITION REQUIRES USE OF HANDS OR SPECIAL TOOLS/EQUIPMENT FOR:')
    #     For tools/equipment handling identify if each is right/left/both handed and return the text label for the respective tool/equipment.
    #     give only the below json as output, i dont need any other information/explanation
    #     Give this in the format:
    #     {{
    #     "manual_dexterity_requirements": {{
    #         "keyboarding" : {{
    #             "right_hand": "boolean",
    #             "left_hand": "boolean",
    #             "both_hands": "boolean"
    #         }},
    #         "filing": {{
    #             "right_hand": "boolean",
    #             "left_hand": "boolean",
    #             "both_hands": "boolean"
    #         }},
    #         "other_description": "string" ## if any other description in tools write here
    #         }}
    #         }}
    #                 """
    #                 # print("=========", images_converted[found_index], "======")
    #                 manual_dexterity_calculation = await self._askLLM(
    #                     dexerity_prompt,
    #                     images=[images_converted[found_index]],
    #                     model=settings.MODEL_4O,
    #                 )

    # print(
    #     "manual_dexterity_calculation-----",
    #     manual_dexterity_calculation,
    #     "-----",
    # )
    return json_data


def liftingHandlingreqs(json_data: dict) -> dict:
    required_weight_ranges = [
        "11-24 lbs",
        "25-49 lbs",
        "50-74 lbs",
        "75-100 lbs",
        "Over 100 lbs",
    ]

    # Iterate through the lifting_handling_reqs
    for requirement in json_data["physical_activities"]["lifting_handling_reqs"]:
        # Create a set of existing weight ranges
        # existing_weight_ranges = {
        #     range_freq["weight_range"]
        #     for range_freq in requirement.get("range_and_frequency", [])
        # }

        # Add missing weight ranges with frequency as an empty string
        # for weight_range in required_weight_ranges:
        #     if weight_range not in existing_weight_ranges:
        #         requirement["range_and_frequency"].append(
        #             {"weight_range": weight_range, "frequency": ""}
        #         )

        # Remove weight ranges that are not in the required list
        requirement["range_and_frequency"] = [
            range_freq
            for range_freq in requirement["range_and_frequency"]
            if range_freq["weight_range"] in required_weight_ranges
        ]

        # Update the frequency for existing weight ranges
        for range_freq in requirement.get("range_and_frequency", []):
            if (
                "frequency" in range_freq
                and "less than 2 hrs" in range_freq["frequency"].lower()
            ):
                range_freq["frequency"] = "Less than 2 hrs daily"

    for requirement in json_data["physical_activities"]["lifting_handling_reqs"]:
        for range_freq in requirement.get("range_and_frequency", []):
            if (
                "frequency" in range_freq
                and "up to 2 hrs" in range_freq["frequency"].lower()
            ):
                json_data["confidence_scores"]["physical_activities"][
                    "lifting_handling_reqs"
                ] = 0.9
                break
    if json_data["physical_activities"]["lifting_handling_reqs"] == []:
        json_data["physical_activities"]["lifting_handling_reqs"] = staticLiftHandling()
    if json_data["physical_activities"]["lifting_handling_reqs"] == {}:
        json_data["physical_activities"]["lifting_handling_reqs"] = staticLiftHandling()
    return json_data


@retry(max_retries=3, wait_time=3)
async def generalInformationextraction(
    json_data: dict, images_converted: list[bytes]
) -> dict:
    general_information_extraction_llm_output: str = (
        await FileProcessingPiplineHelper.askLLM(
            prompt=PromptBuilder.generalInformationExtractionPrompt(),
            images=[images_converted[0]],
            temperature=settings.MODEL_TEMPERATURE,
            model=LLMModelEnum.MODEL_4O.value,
        )
    )

    general_extraction_json = extract_general_information(
        general_information_extraction_llm_output
    )
    cleaned_data = {
        key: "" if value == "string" else value
        for key, value in general_extraction_json.items()
    }
    json_data["general_information"] = cleaned_data
    return json_data


async def liftinghandlingrerun(
    json_data: dict,
    images_to_str_converted_data: list[str],
    images_converted: list[bytes],
    text_from_images: str,
) -> dict:
    try:
        lift_pattern = (
            r"POSITION REQUIRES EMPLOYEE TO:.*?POSITION REQUIRES USE OF HANDS"
        )
        lift_text: str = await FileProcessingPiplineHelper.searchTextUsingPattern(
            patterns=[lift_pattern], text=text_from_images, group=0
        )
        lines = lift_text.split("\n")
        start_patterns = ["11", "25", "50", "75"]
        required_chars = ["L", "C", "P", "PL"]
        replace_with_empty_string = 0
        for line in lines:
            if any(line.strip().startswith(pattern) for pattern in start_patterns):
                if not any(char in line for char in required_chars):
                    if "x" in line.lower():
                        replace_with_empty_string = 1
                        break
        if replace_with_empty_string == 1:
            for requirement in json_data["physical_activities"][
                "lifting_handling_reqs"
            ]:
                for range_freq in requirement.get("range_and_frequency", []):
                    range_freq["frequency"] = ""

        else:
            lift_handling_index = -1
            for i, element in enumerate(images_to_str_converted_data):
                if (
                    "lift" in element.lower()
                    and "carry" in element.lower()
                    and "push" in element.lower()
                    and "pull" in element.lower()
                ):
                    lift_handling_index = i
                    break
            if lift_handling_index != -1:
                lift_handling_prompt_llm_output: str = (
                    await FileProcessingPiplineHelper.askLLM(
                        prompt=PromptBuilder.liftHandlingrerunPrompt(),
                        images=[images_converted[lift_handling_index]],
                        temperature=settings.MODEL_TEMPERATURE,
                        model=LLMModelEnum.MODEL_4O.value,
                    )
                )
                start_index = lift_handling_prompt_llm_output.find("[")
                end_index = lift_handling_prompt_llm_output.rfind("]")
                if start_index != -1 and end_index != -1 and end_index > start_index:
                    list_str = lift_handling_prompt_llm_output[
                        start_index : (end_index + 1)
                    ]
                    extracted_list = ast.literal_eval(list_str)

                    if extracted_list:
                        json_data["physical_activities"]["lifting_handling_reqs"] = (
                            extracted_list
                        )

    except Exception:
        pass

    return json_data


def generalPhysicalActivitiesCheck(json_data: dict) -> dict:
    for requirement in json_data.get("physical_activities", {}).get(
        "general_physical_reqs", []
    ):
        if "type" in requirement:
            requirement["type"] = requirement["type"].lower()

    for requirement in json_data.get("physical_activities", {}).get(
        "general_physical_reqs", []
    ):
        if "type" in requirement:
            if (
                requirement["activity"] == "drive_motor_vehicle"
                and requirement["hours"] == 0
            ):
                requirement["type"] = ""
            else:
                requirement["type"] = requirement["type"].lower()

            if (
                requirement["activity"] == "drive_motor_vehicle"
                and requirement["hours"] == ""
            ):
                requirement["hours"] = 0
                requirement["type"] = ""
            else:
                requirement["type"] = requirement["type"].lower()

    for requirement in json_data.get("physical_activities", {}).get(
        "lifting_handling_reqs", []
    ):
        for range_freq in requirement.get("range_and_frequency", []):
            if (
                "frequency" in range_freq
                and "less than 2 hrs" in range_freq["frequency"].lower()
            ):
                range_freq["frequency"] = "Less than 2 hrs daily"
    return json_data


def positionSummaryConfidenceCheck(json_data: dict, text: str) -> dict:
    if json_data["confidence_scores"]["position_summary"] < 0.95:
        position_pattern = r"position summary(.*?)duties & responsibilities"
        match = re.search(position_pattern, text.lower(), re.DOTALL)

        if match:
            extracted_text = match.group(1).strip()

            extracted_words = set(extracted_text.split())
            position_summary_words = set(json_data["position_summary"].split())

            matching_words = extracted_words & position_summary_words
            matching_percentage = len(matching_words) / len(position_summary_words)
            if matching_percentage >= 0.85:
                json_data["confidence_scores"]["position_summary"] = 0.95

    return json_data


def zonedefinitionfactorConfidenceCheck(json_data: dict, text: str) -> dict:
    if json_data["confidence_scores"]["zone_definition_factors"] < 0.95:
        factors_to_check = []

        for factor_info in json_data["zone_definition_factors"]:
            if factor_info["description"]:
                factors_to_check.append(factor_info["factor"].lower())

        blank_descriptions = sum(
            1
            for factor in json_data.get("zone_definition_factors", [])
            if not factor.get("description")
        )
        if blank_descriptions < 1:
            text_lower = text.lower()
            if all(factor in text_lower for factor in factors_to_check):
                json_data["confidence_scores"]["zone_definition_factors"] = 0.95

    return json_data


def liftHandlingConfidence(json_data: dict) -> dict:
    confidence: dict = json_data.get("confidence_scores")
    physical_activities: dict = confidence.get("physical_activities")
    lifting_handling_reqs = physical_activities.get("lifting_handling_reqs")

    if lifting_handling_reqs < 0.85:

        def count_low_scores(score) -> int:
            if isinstance(score, (float, int)):
                return 1 if score < 0.85 else 0
            elif isinstance(score, dict):
                return sum(count_low_scores(v) for v in score.values())
            return 0

        low_scores = count_low_scores(confidence)

        if low_scores == 1:
            physical_activities["lifting_handling_reqs"] = 0.85

    return json_data


def checkSuperVisionForDict(json_data: dict) -> dict:
    supervision = json_data.get("supervision")
    json_data["supervision"] = str(supervision)
    return json_data
