import os

from azure.identity import ClientSecretCredential
from azure.keyvault.secrets import SecretClient
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


credentials_azure = ClientSecretCredential(
    tenant_id=os.getenv("TENANT-ID"),
    client_id=os.getenv("CLIENT-ID"),
    client_secret=os.getenv("CLIENT-SECRET"),
)

key_vault_client = SecretClient(
    vault_url=f"https://{os.getenv('VAULT-NAME')}.vault.azure.net/",
    credential=credentials_azure,
)


class Settings(BaseSettings):
    ORIGINS: list = ["*"]
    APP_ENVIRONMENT: str = (
        os.getenv("APP-ENVIRONMENT")
        or key_vault_client.get_secret("APP-ENVIRONMENT").value
    )

    # Mongodb
    MONGO_DB_CONNECTION_URL: str = (
        os.getenv("MONGO-DB-CONNECTION-URL")
        or key_vault_client.get_secret("MONGO-DB-CONNECTION-URL").value
    )

    DATABASE_NAME: str = key_vault_client.get_secret("DATABASE-NAME").value

    # storageservices
    STORAGE_SERVICE_URL: str = (
        os.getenv("STORAGE-SERVICE-URL")
        or key_vault_client.get_secret("STORAGE-SERVICE-URL").value
    )
    STORAGE_SERVICE_URL_TOKEN: str = key_vault_client.get_secret(
        "STORAGE-SERVICE-URL-TOKEN"
    ).value
    STORAGE_NAME: str = key_vault_client.get_secret("STORAGE-NAME").value
    CONTAINER_NAME: str = key_vault_client.get_secret("CONTAINER-NAME").value

    # Azure OpenAI
    AZURE_OPENAI_ENDPOINT: str = key_vault_client.get_secret(
        "AZURE-OPENAI-ENDPOINT"
    ).value
    AZURE_OPENAI_KEY: str = key_vault_client.get_secret("AZURE-OPENAI-KEY").value
    AZURE_OPENAI_API_VERSION: str = key_vault_client.get_secret(
        "AZURE-OPENAI-API-VERSION"
    ).value

    # Azure Service Bus
    AZURE_SERVICE_BUS_CONNECTION_STRING: str = key_vault_client.get_secret(
        "AZURE-SERVICE-BUS-CONNECTION-STRING"
    ).value
    AZURE_SERVICE_BUS_QUEUE_NAME: str = (
        os.getenv("AZURE-SERVICE-BUS-QUEUE-NAME")
        or key_vault_client.get_secret("AZURE-SERVICE-BUS-QUEUE-NAME").value
    )

    # model available
    MODEL_4O_MINI: str = os.getenv("4O-MINI-MODEL") or "gpt-4o-mini"
    MODEL_4O: str = os.getenv("4O-MODEL") or "gpt-4o"
    MODEL_TEMPERATURE: float = os.getenv("MODEL-TEMPERATURE") or 0.2
