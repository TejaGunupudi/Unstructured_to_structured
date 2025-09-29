from nebraska_pipeline.storage import (  # noqa: F401  # noqa: F401
    azure_service_bus_client,
    storage,
)
from nebraska_pipeline.utils.constants import Constants


class PreProcessingHelpers:
    @classmethod
    async def validateTemplate(cls, text: str) -> bool:
        keywords_lower = [
            keyword.lower() for keyword in Constants.validTemplateKeywords()
        ]
        found_count = sum(1 for keyword in keywords_lower if keyword in text.lower())
        if (
            found_count / len(Constants.validTemplateKeywords())
            >= Constants.REQUIRED_PERSENTAGE_VALIDTEMPLATE
        ):
            return True
        return False
