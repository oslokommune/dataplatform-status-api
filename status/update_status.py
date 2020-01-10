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

    item = db.update_status(statusid, content)
    if item is None:
        return response(404, json.dumps({"error": "Could not update item"}))

    return response(200, json.dumps("Status is updated"))


def response(code, body):
    return {
        "statusCode": code,
        "body": body,
    }
