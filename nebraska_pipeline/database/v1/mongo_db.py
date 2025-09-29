from bson import ObjectId
from pymongo.collection import Collection
from pymongo.synchronous.client_session import ClientSession

from nebraska_pipeline.utils.utilities import convertToPythonDict


class MongoDBOperation:
    @staticmethod
    def readOne(
        collection_instance: Collection, filter: dict, other: dict | list
    ) -> dict:
        data: list = collection_instance.find_one(filter, other)
        return convertToPythonDict(data=data)

    @staticmethod
    def readMany(
        collection_instance: Collection,
        filter: dict,
        other: dict | list,
        sort: dict = {"_id": 1},
        skip: int = 0,
        limit: int = 0,
    ) -> list[dict]:
        data: list = list(
            collection_instance.find(filter, other).skip(skip).limit(limit).sort(sort)
        )
        return convertToPythonDict(data=data)

    @staticmethod
    def insertOne(collection_instance: Collection, data: dict) -> str:
        return str(collection_instance.insert_one(data).inserted_id)

    @staticmethod
    def insertOneSyncronus(
        collection_instance: Collection, data: dict, session: ClientSession
    ) -> str:
        return str(collection_instance.insert_one(data, session=session).inserted_id)

    @staticmethod
    def insertMany(collection_instance: Collection, data: dict) -> str:
        insert_data = collection_instance.insert_many(data)
        return [str(i) for i in insert_data.inserted_ids]

    @staticmethod
    def updateOne(
        collection_instance: Collection,
        object_id: str,
        data: dict,
    ):
        return collection_instance.update_one(
            {"_id": ObjectId(object_id)},
            {"$set": data},
        )

    @staticmethod
    def updateOneWithUpsert(
        collection_instance: Collection,
        filter: dict,
        data: dict,
    ):
        return collection_instance.update_one(filter, {"$set": data}, upsert=True)

    @staticmethod
    def deleteOne(collection_instance: Collection, filter: dict):
        return convertToPythonDict(collection_instance.find_one_and_delete(filter))

    @staticmethod
    def deleteMany(collection_instance: Collection, filter: dict):
        return collection_instance.delete_many(filter=filter)
