from azure.servicebus import ServiceBusClient

from nebraska_pipeline import settings
from nebraska_pipeline.storage.azure_service_bus import AzureServiceBus
from nebraska_pipeline.storage.azure_storage import StorageServices

storage: StorageServices = StorageServices(
    storage_services_url=settings.STORAGE_SERVICE_URL,
    storage_services_token=settings.STORAGE_SERVICE_URL_TOKEN,
    storage_name=settings.STORAGE_NAME,
    container_name=settings.CONTAINER_NAME,
)

azure_service_bus_client: AzureServiceBus = AzureServiceBus(
    service_bus_client=ServiceBusClient.from_connection_string(
        conn_str=settings.AZURE_SERVICE_BUS_CONNECTION_STRING
    ),
    queue_name=settings.AZURE_SERVICE_BUS_QUEUE_NAME,
)
