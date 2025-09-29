import datetime
import json
import os
import re
import time
from time import mktime

import bson
import bson.errors
from bson import ObjectId


def removeFile(path) -> None:
    os.remove(path)


def convertToPythonDict(data: list | dict) -> dict | list:
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, ObjectId):
                data[key] = str(value)
            elif isinstance(value, (dict, list)):
                convertToPythonDict(value)
    elif isinstance(data, list):
        for index, item in enumerate(data):
            if isinstance(item, ObjectId):
                data[index] = str(item)
            elif isinstance(item, (dict, list)):
                convertToPythonDict(item)
    return data


def convertToObjectID(data: list | dict) -> dict | list:
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, str):
                try:
                    data[key] = ObjectId(value)
                except bson.errors.InvalidId:
                    pass
            elif isinstance(value, (dict, list)):
                convertToObjectID(value)
    elif isinstance(data, list):
        for index, item in enumerate(data):
            if isinstance(item, str):
                try:
                    data[index] = ObjectId(item)

                except bson.errors.InvalidId:
                    pass
            elif isinstance(item, (dict, list)):
                convertToObjectID(item)
    return data


def convertEpocTimeToDateTime(epoc_time_stamp: int) -> datetime.datetime:
    if isinstance(epoc_time_stamp, float) is False:
        raise TypeError(
            f"input epoc_time_stamp should be type int but got {type(epoc_time_stamp)}"
        )
    return datetime.datetime.fromtimestamp(epoc_time_stamp).date()


def convertDateToEpocTimeStamp(
    date: datetime.date = datetime.datetime.now().date(),
    time: datetime.time = datetime.datetime.now().time(),
) -> int:
    if isinstance(date, datetime.date) is False:
        raise TypeError(f"input date should be type date but got {type(date)}")

    if isinstance(time, datetime.time) is False:
        raise TypeError(f"input date should be type date but got {type(time)}")

    datetime_combined: datetime.datetime = datetime.datetime.combine(
        date=date, time=time
    )
    # return datetime_combined, int(mktime(datetime_combined.timetuple()))
    return int(mktime(datetime_combined.timetuple()))


def convertObjectToPythonDateTime(data: list | dict) -> dict | list:
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(key, str) and "date" in key.split("_"):
                try:
                    data[key] = convertEpocTimeToDateTime(float(value))
                except Exception:
                    data[key] = value
            elif isinstance(value, (dict, list)):
                convertObjectToPythonDateTime(value)
    elif isinstance(data, list):
        for index, item in enumerate(data):
            if isinstance(index, str) and "date" in index.split("_"):
                try:
                    data[index] = convertEpocTimeToDateTime(float(item))
                except Exception:
                    data[index] = item
            elif isinstance(item, (dict, list)):
                convertObjectToPythonDateTime(item)
    return data


def extract_json_from_string(text):
    # Use regular expression to find the substring between '{' and '}'
    match = re.search(r"\{.*?\}", text, re.DOTALL)
    if match:
        json_str = match.group(0)
        try:
            # Convert the extracted string to JSON
            json_data = json.loads(json_str)
            return json_data
        except json.JSONDecodeError:
            # print(f"Error decoding JSON: {e}")
            return None
    else:
        # print("No JSON object found in the string")
        return None


def extract_general_information(text: str):
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        json_str = match.group(0)
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            try:
                json_str = re.sub(r":\s*(\d+)", r': "\1"', json_str)
                return json.loads(json_str)
            except json.JSONDecodeError:
                return None
    else:
        return None


def retry(max_retries, wait_time):
    def decorator(func):
        def wrapper(*args, **kwargs):
            retries = 0
            if retries < max_retries:
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception:
                    retries += 1
                    time.sleep(wait_time)
            else:
                raise Exception(f"Max retries of function {func} exceeded")

        return wrapper

    return decorator
