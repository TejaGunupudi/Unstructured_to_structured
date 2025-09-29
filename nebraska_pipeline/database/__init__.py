from pymongo import MongoClient
from pymongo.collection import Collection

from nebraska_pipeline import settings
from nebraska_pipeline.database.v1 import MongoDBOperation
from nebraska_pipeline.utils.exceptions import MongoDBConnectionError

try:
    client_instance: MongoClient = MongoClient(settings.MONGO_DB_CONNECTION_URL)

    user_collection_instance: Collection = client_instance[settings.DATABASE_NAME][
        "users"
    ]
    file_collection_instance: Collection = client_instance[settings.DATABASE_NAME][
        "files"
    ]
    json_data_collection_instance: Collection = client_instance[settings.DATABASE_NAME][
        "jsonData"
    ]

except Exception as e:
    raise MongoDBConnectionError(exception=e)


mongo_instance: MongoDBOperation = MongoDBOperation()
