# import asyncio
# import datetime
# import json
# import traceback

# from bson import ObjectId

# from nebraska_pipeline.controller.helpers import (
#     ProcessingPiplineHelperMethods,
# )
# from nebraska_pipeline.controller.v1 import FileProcessingPipelineController
# from nebraska_pipeline.database import (
#     file_collection_instance,
#     json_data_collection_instance,
#     mongo_instance,
# )
# from nebraska_pipeline.storage import azure_service_bus_client, storage  # noqa: F401
# from nebraska_pipeline.utils.app_logs import log_handler
# from nebraska_pipeline.utils.enums import ConfidenceEnum, StatusEnum


# async def processFile():
#     message = azure_service_bus_client.getMessageFromQueue()
#     if message is None:
#         log_handler.warning("No files to download exiting")
#         return
#     log_handler.info(f" message : {str(message)}")
#     unprocessed_file: dict = json.loads(str(message))
#     file_id = unprocessed_file.get("file_id")

#     try:
#         file_details: dict | None = mongo_instance.readOne(
#             collection_instance=file_collection_instance,
#             filter={"_id": ObjectId(file_id)},
#             other={},
#         )
#         if file_details is None or file_details.get("status") != StatusEnum.QUEUED:
#             log_handler.info("File Not Found or already processed")
#             return
#         file_data: bytes = await storage.getBlobFromAzure(
#             file_blob_url=file_details.get("file_url")
#         )
#         file_name: str = file_details.get("file_name")

#         mongo_instance.updateOne(
#             collection_instance=file_collection_instance,
#             object_id=file_id,
#             data={
#                 "status": StatusEnum.PROCESSING.value,
#                 "process_started_at": int(datetime.datetime.now().timestamp()),
#             },
#         )
#         (
#             report,
#             json_extracted_data,
#         ) = await FileProcessingPipelineController().processFile(
#             file_data=file_data, file_name=file_name
#         )
#         json_extracted_data["file_name"] = file_name

#         json_data: dict = {
#             "json_data": json_extracted_data,
#             "confidence": report,
#             "json_data_edited": {},
#             "is_json_edited": False,
#             "created_at": int(datetime.datetime.now().timestamp()),
#             "updated_at": int(datetime.datetime.now().timestamp()),
#         }
#         overall_confidence = await ProcessingPiplineHelperMethods.overalConfidence(
#             confidence_score=report
#         )
#         mongo_instance.updateOneWithUpsert(
#             collection_instance=json_data_collection_instance,
#             filter={"file_id": str(file_id)},
#             data=json_data,
#         )

#         mongo_instance.updateOne(
#             collection_instance=file_collection_instance,
#             object_id=file_id,
#             data={
#                 "status": StatusEnum.COMPLETED.value,
#                 "process_completed_at": int(datetime.datetime.now().timestamp()),
#                 "is_json_ready_for_export": overall_confidence
#                 in [
#                     ConfidenceEnum.HIGH,
#                     ConfidenceEnum.MEDIUM,
#                 ],
#                 "updated_at": int(datetime.datetime.now().timestamp()),
#                 "is_json_exported": False,
#                 "overall_confidence": overall_confidence,
#             },
#         )

#         log_handler.info(f"Processing completed for file: {file_name}")

#     except Exception as e:
#         log_handler.exception(traceback.format_exc())
#         log_handler.error(f"Error processing file {file_name}: {e}")
#         mongo_instance.updateOne(
#             collection_instance=file_collection_instance,
#             object_id=file_id,
#             data={
#                 "status": StatusEnum.FAILED.value,
#                 "overall_confidence": None,
#                 "error_log": f"[error] : {type(e)} : [detail] : {str(e)}",
#                 "process_completed_at": int(datetime.datetime.now().timestamp()),
#                 "updated_at": int(datetime.datetime.now().timestamp()),
#             },
#         )

#     finally:
#         azure_service_bus_client.acknowledgeMessage(msg=message)

#     log_handler.info("Background process finished.")


# if __name__ == "__main__":
#     asyncio.run(processFile())

# nebraska_main:
import asyncio
import json
import os

from nebraska_pipeline.controller.v1 import FileProcessingPipelineController
from nebraska_pipeline.storage import azure_service_bus_client, storage  # noqa: F401
from nebraska_pipeline.utils.app_logs import log_handler

# async def processFile():
#     message = azure_service_bus_client.getMessageFromQueue()
#     if message is None:
#         return
#     log_handler.info(f" message : {str(message)}")
#     unprocessed_file: dict = json.loads(str(message))
#     file_id = unprocessed_file.get("_id")
#     file_name = unprocessed_file.get("file_name")
#     file_url = unprocessed_file.get("file_url")

#     try:
#         file_data: bytes = await storage.getBlobFromAzure(file_blob_url=file_url)

#         mongo_instance.updateOne(
#             collection_instance=file_collection_instance,
#             object_id=file_id,
#             data={
#                 "status": StatusEnum.PROCESSING.value,
#                 "process_started_at": int(datetime.datetime.now().timestamp()),
#             },
#         )
#         (
#             report,
#             json_extracted_data,
#         ) = await FileProcessingPipelineController().processFile(
#             file_data=file_data, file_name=file_name
#         )
#         json_extracted_data["file_name"] = file_name

#         json_data: dict = {
#             "json_data": json_extracted_data,
#             "confidence": report,
#             "json_data_edited": {},
#             "is_json_edited": False,
#             "overal_confidence": await ProcessingPiplineHelperMethods.overalConfidence(
#                 confidence_score=report
#             ),
#             "created_at": int(datetime.datetime.now().timestamp()),
#             "updated_at": int(datetime.datetime.now().timestamp()),
#         }

#         mongo_instance.updateOneWithUpsert(
#             collection_instance=json_data_collection_instance,
#             filter={"file_id": str(file_id)},
#             data=json_data,
#         )

#         mongo_instance.updateOne(
#             collection_instance=file_collection_instance,
#             object_id=file_id,
#             data={
#                 "status": StatusEnum.COMPLETED.value,
#                 "process_completed_at": int(datetime.datetime.now().timestamp()),
#                 "is_json_ready_for_export": ProcessingPiplineHelperMethods.checkIfJsonIsReadyForExport(
#                     report=report
#                 ),
#                 "updated_at": int(datetime.datetime.now().timestamp()),
#             },
#         )

#         log_handler.info(f"Processing completed for file: {file_name}")

#     except Exception as e:
#         log_handler.exception(traceback.format_exc())
#         log_handler.error(f"Error processing file {file_name}: {e}")
#         mongo_instance.updateOne(
#             collection_instance=file_collection_instance,
#             object_id=file_id,
#             data={
#                 "status": StatusEnum.FAILED.value,
#                 "error_log": f"[error] : {type(e)} : [detail] : {str(e)}",
#                 "process_completed_at": int(datetime.datetime.now().timestamp()),
#                 "updated_at": int(datetime.datetime.now().timestamp()),
#             },
#         )

#     finally:
#         azure_service_bus_client.acknowledgeMessage(msg=message)


#     log_handler.info("Background process finished.")
async def processFile():
    try:
        directory_name: str = r"test_files/"
        file_name: str = "56013   Research Technician, Biology.pdf"
        with open(
            f"{directory_name}/{file_name}",
            "br",
        ) as file:
            file_data: bytes = file.read()
        os.makedirs("output_json", exist_ok=True)
        report, result_json = await FileProcessingPipelineController().processFile(
            file_data=file_data, file_name=file_name
        )

        with open(
            f"./output_json/{file_name}.json", "w", encoding="utf-8"
        ) as temp_json_file:
            json.dump(
                result_json,
                temp_json_file,
                default=str,
                indent=4,
                ensure_ascii=False,
            )
        with open(
            f"./output_json/{file_name}_report.json", "w", encoding="utf-8"
        ) as temp_json_file:
            json.dump(
                report,
                temp_json_file,
                default=str,
                indent=4,
                ensure_ascii=False,
            )
        result_json["confidence_scores"] = report
        file_name_short_index = file_name.rfind(".")
        if file_name_short_index != -1:
            file_name_short = file_name[:file_name_short_index]

        old_json_path = os.path.join("json_files", f"{file_name_short}.json")
        if os.path.exists(old_json_path):
            with open(old_json_path, encoding="utf-8") as old_file:
                old_json = json.load(old_file)
            from deepdiff import DeepDiff

            diff = DeepDiff(old_json, result_json, ignore_order=True)
            if diff:
                # If there are differences, you can print/log them

                print(result_json)
                print("............................................")
                print("Differences found between the old JSON and the new result_json:")
                print("------------------", diff)

            else:
                print("No differences found. Both JSONs appear to be the same.")
        else:
            print(
                f"No existing JSON found for {file_name_short}, so nothing to compare."
            )
            print("original json: ................", result_json)

    except Exception as e:
        log_handler.error(e)


if __name__ == "__main__":
    asyncio.run(processFile())
