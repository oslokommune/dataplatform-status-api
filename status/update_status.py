import json
import logging
from status.StatusData import StatusData

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
        return response(404, json.dumps(f"Could not find the requested item to update: {statusid}"))


def response(code, body):
    return {
        "statusCode": code,
        "body": body,
    }
