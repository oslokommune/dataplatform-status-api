import json
import logging
from botocore.exceptions import ClientError
from status.common import response, response_error, is_owner
from status.StatusData import StatusData

log = logging.getLogger()
log.setLevel(logging.INFO)


def handler(event, context):
    params = event["pathParameters"]
    statusid = params["statusid"]
    db = StatusData()

    try:
        item = db.get_status(id=statusid)

        if item is None:
            error = f"Could not find item: {statusid}"
            return response_error(404, error)

        items = item["Items"]
        if is_owner(event, items[0]) is False:
            log.info(f"User tried to get status but was denied: {items[0]}")
            return response_error(403, "Access denied")
        return response(200, json.dumps(items))

    except ClientError as ce:
        log.info(f"ClientError: {ce}")
        error = f"Could not get status: {ce}"
        return response_error(404, error)
