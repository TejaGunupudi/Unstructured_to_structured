from enum import StrEnum

from nebraska_pipeline import settings


class StatusEnum(StrEnum):
    COMPLETED = "completed"
    PROCESSING = "processing"
    QUEUED = "queued"
    FAILED = "failed"


class ConfidenceEnum(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ZoneDefinitionFactorsEnum(StrEnum):
    NATURE_OR_COMPLEXITY_OF_WORK = "Nature/Complexity of Work"
    PROBLEM_SOLVING_DECISION_MAKING = "Problem Solving/Decision-making"
    STRATEGIC_IMPACT = "Strategic Impact"
    KNOW_HOW = "Know How"
    TECHNICAL_KNOW_HOW = "Technical Know How"
    INTERACTIONS = "Interactions"
    LEADERSHIP = "Leadership"


class GeneralPhysicalRequirementsActivityEnum(StrEnum):
    SITTING = "sitting"
    STANDING = "standing"
    WALKING = "walking"
    DRIVE_MOTOR_VEHICLE = "drive_motor_vehicle"


class SpecificPhysicalRequirementsActivityEnum(StrEnum):
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


class LiftingAndHandelingRequirementsActivityType(StrEnum):
    LIFT = "lift"
    CARRY = "carry"
    PUSH = "push"
    PULL = "pull"


class ManualDexterityRequirementsTaskEnum:
    KEYBOARDING = "keyboarding"
    FILING = "filing"


class LLMModelEnum(StrEnum):
    MODEL_4O_MINI = settings.MODEL_4O_MINI
    MODEL_4O = settings.MODEL_4O


class WordsMissingEnum(StrEnum):
    KEYBOARDING = "keyboarding"
    FILING = "filing"


# below are the key enums of the schema
class JsonDataKeyEnum(StrEnum):
    APPLICATION_PROCEDURE = "application_procedure"
    ADDITIONAL_INFORMATION = "additional_information"
    QUALIFICATIONS_AND_ATTRIBUTES = "qualifications_and_attributes"
    SUPERVISION = "supervision"
    PHYSICAL_ACTIVITIES = "physical_activities"


class PhysicalActivitesTypeEnum(StrEnum):
    SPECIFIC_PHYSICAL_REQS = "specific_physical_reqs"
