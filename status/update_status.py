import json
import logging
from status.StatusData import StatusData
from status.common import response, response_error, is_owner

log = logging.getLogger()
log.setLevel(logging.INFO)


def handler(event, context):
    params = event["pathParameters"]
    statusid = params["statusid"]

    content = json.loads(event["body"])

    db = StatusData()
    result = db.get_status(statusid)
    items = result["Items"]

    if len(items) != 0:
        if is_owner(event, items[0]) is False:
            log.info(f"User tried to get status but was denied: {items[0]}")
            return response_error(403, "Access denied")
        item = db.update_status(statusid, content)
        return response(200, json.dumps(item))
    error = f"Could not find the requested item to update: {statusid}"
    return response_error(404, error)
