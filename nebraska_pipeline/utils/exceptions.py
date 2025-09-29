class MongoDBConnectionError(Exception):
    def __init__(self, detail="MongoDB Connection Failed", exception: str = None):
        super().__init__(f"{detail} : {exception}")


class InternalServerError(Exception):
    def __init__(self, status_code: int = 500, detail: str = None):
        super().__init__(f"{status_code} : {detail}")


class FileNotSupportedError(Exception):
    def __init__(self, detail: str = "File not supported"):
        super().__init__(detail)
