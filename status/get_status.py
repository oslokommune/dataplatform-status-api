import json
import logging
from status.StatusData import StatusData

log = logging.getLogger()
log.setLevel(logging.INFO)


def handler(event, context):
    params = event["pathParameters"]
    uuid = params["uuid"]
    db = StatusData()
    item = db.get_status(id=uuid)

    item = db.get_status(uuid)
    if item is None:
        return response(404, json.dumps({"error": "Could not find item"}))
    else:
        return response(200, json.dumps(item))


def response(code, body):
    return {
        "statusCode": code,
        "body": body,
        "headers": {"Access-Control-Allow-Origin": "*"},
    }
