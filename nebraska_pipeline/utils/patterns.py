from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class Patterns:
    PATTERN: Literal["r"] = (
        r"Circle the appropriate number of hours Intermittent Constant(.*?)(?=Explain)"
    )
    GENERAL_PHYSICAL_ACTIVITY_PATTERN_V2: Literal["r"] = (
        r"Circle the appropriate number Intermitte Constant(.*?)(?=Explain)"
    )
    ATTENDANCE_PATTERN: Literal["r"] = (
        r"(.{0,10}REQUIRES:ATTENDANCE AT THE WORKPLACE(.*?)NON-ESSENTIAL(.{0,10}))"
    )
    ATTENDANCE_PATTERN_V2: Literal["r"] = (
        r"(.{0,10}REQUIRES ATTENDANCE AT THE WORKPLACE(.*?)NON-ESSENTIAL(.{0,10}))"
    )
    JSON_EXTRACT_FROM_LLM_RESPOSNE_PATTERN: Literal["r"] = r"\{.*\}"
    EXTRACT_JSON_RESPONCE_GREEDY: Literal["r"] = r"\{.*?\}"
    POSITION_SUMMARY_PATTERN: Literal["r"] = (
        r"(?<=Position Sum)[\s\S]+?(?=Section|Duties & Responsibilities|%|Duties|Indicate)"
    )
    SPECIFIC_PHYSICAL_REQS_TEXT_DATA_PATTERN: Literal["r"] = (
        r"THIS JOB REQUIRES EMPLOYEE TO:.*?THIS JOB REQUIRES EMPLOYEE TO:"
    )
    OVERHEAD: Literal["r"] = r"overhead.*"
