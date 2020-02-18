import json
import logging
import base64
from auth import SimpleAuth
from botocore.exceptions import ClientError

from status.StatusData import StatusData

log = logging.getLogger()
log.setLevel(logging.INFO)

error_message = {"error": "Could not find item"}


def is_owner(event, item):
    if item["application"] == "dataset":
        dataset_id = item["application_id"]
        return SimpleAuth().is_owner(event, dataset_id)
    return False


def handler(event, context):
    params = event["pathParameters"]
    # The s3path parameter MUST be base64 encoded since it can contain "/"
    # and any other character known to man.....
    path = base64.b64decode(params["s3path"]).decode("utf-8", "ignore")
    db = StatusData()

    try:
        item = db.get_status_from_s3_path(path)

        if item is None:
            return response(404, json.dumps(error_message))
        else:
            if is_owner(event, item):
                ret = {"id": item["id"]}
                return response(200, json.dumps(ret))
            return response(403, json.dumps({"error": "Access denied"}))

    except ClientError as ce:
        log.info(f"ClientError: {ce}")
        return response(404, json.dumps(error_message))


def response(code, body):
    return {
        "statusCode": code,
        "body": body,
        "headers": {"Access-Control-Allow-Origin": "*"},
    }
