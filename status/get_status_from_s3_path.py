import json
import logging
import base64
from botocore.exceptions import ClientError

from status.StatusData import StatusData
from status.common import response, response_error, is_owner

log = logging.getLogger()
log.setLevel(logging.INFO)


def handler(event, context):
    params = event["pathParameters"]
    # The s3path parameter MUST be base64 encoded since it can contain "/"
    # and any other character known to man.....
    path = base64.b64decode(params["s3path"]).decode("utf-8", "ignore")
    log.info(f"path from base64 encoded parameter: {path}")
    db = StatusData()

    try:
        item = db.get_status_from_s3_path(path)
        log.info(f"db.get_status_from_s3_path returned: {item}")
        if item is None:
            error = "Could not find item"
            return response_error(404, error)

        if is_owner(event, item):
            ret = {"id": item["id"]}
            log.info(f"Found owner for item and returning: {ret}")
            return response(200, json.dumps(ret))
        error = "Access denied"
        log.info(f"is_owner() failed with event: {event} on item: {item} ")
        return response_error(403, error)

    except ClientError as ce:
        log.info(f"ClientError: {ce}")
        error = f"Could not get status: {ce}"
        return response_error(404, error)
