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

    item, event_id = db.update_status(statusid, content)
    if item is None:
        return response(404, json.dumps({"error": "Could not update item"}))

    responsebody = {"event_id": event_id, "item": content}
    return response(200, json.dumps(responsebody))


def response(code, body):
    return {
        "statusCode": code,
        "body": body,
    }
