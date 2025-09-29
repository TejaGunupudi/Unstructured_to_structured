from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class WeightRange(StrEnum):
    RANGE_11_24 = "11-24 lbs"
    RANGE_25_49 = "25-49 lbs"
    RANGE_50_74 = "50-74 lbs"
    RANGE_75_100 = "75-100 lbs"
    OVER_100 = "Over 100 lbs"


class GeneralPhysicalActivityType(StrEnum):
    SITTING = "sitting"
    STANDING = "standing"
    WALKING = "walking"
    DRIVE_MOTOR_VEHICLE = "drive_motor_vehicle"


class LiftActivityType(StrEnum):
    LIFT = "lift"
    CARRY = "carry"
    PUSH = "push"
    PULL = "pull"


class QualificationType(StrEnum):
    HELPFUL = "helpful_qualifications"
    MINIMUM = "minimum_qualifications"
    OTHER = "other_information"
    PREFERRED = "preferred_qualifications"
    REQUIRED = "required_qualifications"


class SpecificPhysicalRequirementsActivityType(StrEnum):
    SQUATTING = "squating"
    BENDING = "bending"
    KNEELING = "kneeling"
    REACHING_OVERHEAD = "reaching_overhead"
    REACHING_FORWARD = "reaching_forward"
    REACHING_LOW = "reaching_low"
    TWISTING = "twisting"
    CRAWLING = "crawling"
    CLIMBING_LADDERS = "climbing_ladders"
    CLIMBING_STAIRS = "climbing_stairs"
    CLIMBING_OTHER = "climbing_other"
    WALKING_ON_ROUGH_GROUND = "walking_on_rough_ground"
    EXPOSURE_TO_CHANGES_OF_TEMPERATURE_HUMIDITY = (
        "exposure_to_changes_of_temperature_humidity"
    )
    EXPOSURE_TO_DUST_FUMES_GASES_CHEMICALS = "exposure_to_dust_fumes_gases_chemicals"
    BEING_NEAR_MOVING_MACHINERY = "being_near_moving_machinery"
    WORKING_FROM_HEIGHTS = "working_from_heights"


class ZoneDefinitionFactorsEnum(StrEnum):
    NATURE_OR_COMPLEXITY_OF_WORK = "Nature/Complexity of Work"
    PROBLEM_SOLVING_DECISION_MAKING = "Problem Solving/Decision-making"
    STRATEGIC_IMPACT = "Strategic Impact"
    KNOW_HOW = "Know How"
    TECHNICAL_KNOW_HOW = "Technical Know How"
    INTERACTIONS = "Interactions"
    LEADERSHIP = "Leadership"


class ManualDexterity(BaseModel):
    both_hands: bool
    left_hand: bool
    right_hand: bool


class GeneralPhysicalRequisites(BaseModel):
    activity: GeneralPhysicalActivityType
    hours: int = Field(..., ge=0, le=24)
    type: str


class PhysicalActivityRangeaAndFrequency(BaseModel):
    weight_range: WeightRange
    frequency: str


class LiftingHandlingReq(BaseModel):
    activity_type: LiftActivityType
    range_and_frequency: list[PhysicalActivityRangeaAndFrequency]


class ManualDexterityReqs(BaseModel):
    filing: ManualDexterity
    keyboarding: ManualDexterity
    other_description: str
    model_config = ConfigDict(extra="allow")


class SpecificPhysicalRequisites(BaseModel):
    activity: SpecificPhysicalRequirementsActivityType
    frequency: str


class WorkAttendanceReqs(BaseModel):
    must_attend_workplace: bool
    alt_worksite_eligible: bool
    wfo_essential: bool
    wfo_non_essential: bool


class ZoneDefinitionFactor(BaseModel):
    factor: ZoneDefinitionFactorsEnum
    description: str


class DutiesAndResponsibility(BaseModel):
    responsibility: str
    time_spent_percentage: int = Field(..., ge=0, le=100)
    essential_function: bool
    tasks: list[str]


class QualificationsAndAttributes(BaseModel):
    required_qualifications: list[str]
    preferred_qualifications: list[str]
    helpful_qualifications: list[str]
    minimum_qualifications: list[str]
    other_information: list[str]


class GeneralInformation(BaseModel):
    working_job_title: str
    job_family: str
    job_family_zone: str  # job_family_zone and job_code are the same, as mentioned
    position_number: int | str
    department_name: str
    SAP_organization_unit_number: str
    employee_name: str
    date_of_last_update: str | datetime = Field(..., description="MMDDYYYY")
    last_updated_by: str
    title_of_supervisor: str
    sap_personnel: str
    name_of_supervisor: str


class PhysicalActivities(BaseModel):
    general_physical_reqs: list[GeneralPhysicalRequisites]
    specific_physical_reqs: list[SpecificPhysicalRequisites]
    lifting_handling_reqs: list[LiftingHandlingReq]
    manual_dexterity_reqs: ManualDexterityReqs
    work_attendance_reqs: WorkAttendanceReqs


class JobPosition(BaseModel):
    general_information: GeneralInformation
    position_summary: str
    duties_and_responsibilities: list[DutiesAndResponsibility]
    supervision: str
    qualifications_and_attributes: QualificationsAndAttributes
    zone_definition_factors: list[ZoneDefinitionFactor]
    physical_activities: PhysicalActivities
    additional_information: str
    application_procedure: str
