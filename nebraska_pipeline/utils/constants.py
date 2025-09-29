from dataclasses import dataclass

from pymupdf import Matrix


@dataclass(frozen=True)
class Constants:
    ZOOM_X: float = 2.5
    ZOOM_Y: float = 2.5
    FX: float = 1.5
    FY: float = 1.5
    ADAPTIVE_THRESHOLD_MAXVALUE: float = 255
    BLOCK_SIZE: float = 11
    ADAPTIVE_THRESHOLD_C_VALUE: float = 2
    FAST_NL_MEANS_H_VALUE: float = 30
    TEMPLATE_WINDOW_SIZE: int = 7
    SEARCH_WINDOW_SIZE: int = 21
    LIMIT_PER_USER: int = 25
    REQUIRED_PERSENTAGE_VALIDTEMPLATE: float = 0.5

    def returnPyMuPDFMatrix(self) -> Matrix:
        return Matrix(self.ZOOM_X, self.ZOOM_Y)

    @classmethod
    def validTemplateKeywords(cls) -> list[str]:
        return [
            "General Information",
            "Position Summary",
            "Duties & Responsibilities",
            "Zone Definition Factors",
            "Strategic Impact",
            "Qualifications",
            "Physical Requirements",
            "General Physical Requirements",
        ]

    @classmethod
    def specificPhysicalReqRequiredKeywords(cls) -> list[str]:
        return [
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
