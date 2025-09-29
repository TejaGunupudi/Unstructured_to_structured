import httpx

from nebraska_pipeline.utils.exceptions import InternalServerError


class StorageServices:
    def __init__(
        self,
        storage_services_url: str,
        storage_services_token: str,
        storage_name: str,
        container_name: str,
        overwrite_file: bool = False,
    ):
        self.STORAGE_SERVICE_URL = storage_services_url
        self.STORAGE_NAME: str = storage_name
        self.CONTAINER_NAME: str = container_name
        self.OVERWRITE_FILE: bool = overwrite_file
        self.headers = {
            "Authorization": f"Bearer {storage_services_token}",
        }

    async def getBlobFromAzure(self, file_blob_url: str) -> bytes:
        url = f"{self.STORAGE_SERVICE_URL}/v1/storage/azure/read"
        params = {"file_blob_url": file_blob_url}

        if not isinstance(file_blob_url, str):
            raise TypeError("file_url have invalid type.")

        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, headers=self.headers)
            if response.status_code != 200:
                raise InternalServerError(
                    status_code=response.status_code,
                    detail=f"Internal error [error]  : {response} : {response.content.decode()}",
                )
            return response.content

    async def getSharedAccessSignatureForContainer(self) -> dict:
        params: dict = {
            "sas_token_for_container": True,
            "storage_name": "base-azure-storage",
            "container_name": self.CONTAINER_NAME,
        }

        url = f"{self.STORAGE_SERVICE_URL}/v1/storage/azure/getSharedAccessSignature"

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers, params=params)

            if response.status_code != 200:
                raise InternalServerError(
                    status_code=response.status_code,
                    detail=f"Internal error [error]  : {response} : {response.content.decode()}",
                )
            return response.json()

    async def getFilterBlobFromAzureContainer(
        self, storage_name: str, container_name: str, filter: dict = {}
    ) -> dict:
        params = {
            "storage_name": storage_name,
            "container_name": container_name,
            "filter": filter,
        }
        url = f"{self.STORAGE_SERVICE_URL}/v1/storage/azure/getFilterdBlob"

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers, params=params)
            if response.status_code != 200:
                raise InternalServerError(
                    status_code=response.status_code, detail=response.json()
                )
            return response.json()

    async def uploadBlobToAzure(
        self, file_name: str, file_data: bytes, folder_structure: str = "files"
    ) -> dict:
        url = f"{self.STORAGE_SERVICE_URL}/v1/storage/azure/upload"
        params = {
            "storage_name": self.STORAGE_NAME,
            "container_name": self.CONTAINER_NAME,
            "file_folder_structure": folder_structure,
            "overwrite_file": self.OVERWRITE_FILE,
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers=self.headers,
                params=params,
                files={"file": (file_name, file_data)},
            )
            if response.status_code != 200:
                raise InternalServerError(
                    status_code=response.status_code,
                    detail=f"Internal error [error]  : {response} : {response.content.decode()}",
                )
            return response.json()

    async def deleteBlobFromAzure(
        self, file_blob_url: str, delete_snapshots: bool = True
    ) -> dict:
        url = f"{self.STORAGE_SERVICE_URL}/v1/storage/azure/deleteFile"

        params = {"file_blob_url": file_blob_url, "delete_snapshots": delete_snapshots}

        async with httpx.AsyncClient() as client:
            response = await client.delete(url, headers=self.headers, params=params)
            if response.status_code != 200:
                raise InternalServerError(
                    status_code=response.status_code,
                    detail=f"Internal error [error]  : {response} : {response.content.decode()}",
                )
            return response.json()

    async def deleteFolderFromAzure(self, folder_path: str) -> dict:
        url = f"{self.STORAGE_SERVICE_URL}/v1/storage/azure/deleteFolder"

        params = {
            "storage_name": self.STORAGE_NAME,
            "container_name": self.CONTAINER_NAME,
            "folder_path": folder_path,
        }

        async with httpx.AsyncClient() as client:
            response = await client.delete(url, headers=self.headers, params=params)
            if response.status_code != 200:
                raise InternalServerError(
                    status_code=response.status_code,
                    detail=f"Internal error [error]  : {response} : {response.content.decode()}",
                )
            return response.json()
