import json
import logging
from status.StatusData import StatusData
from status.common import response, response_error

log = logging.getLogger()
log.setLevel(logging.INFO)


def handler(event, context):
    params = event["pathParameters"]
    statusid = params["statusid"]

    content = json.loads(event["body"])

    db = StatusData()

    if len(db.get_status(statusid)["Items"]) != 0:

        item = db.update_status(statusid, content)
        return response(200, json.dumps(item))
    else:
        error = f"Could not find the requested item to update: {statusid}"
        return response_error(404, error)
