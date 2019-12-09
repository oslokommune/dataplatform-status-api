import json
import logging
from StatusData import StatusData

log = logging.getLogger()
log.setLevel(logging.INFO)


def handler(event, context):
    params = event["pathParameters"]
    uuid = params["uuid"]
    """ny status?"""
    status = params["status"]

    db = StatusData()

    item = db.update_status(uuid, status)
    if item is None:
        return response(404, json.dumps({"error": "Could not find item"}))

    return response(200, json.dumps(item))


def response(code, body):
    return {
        "statusCode": code,
        "body": body,
        "headers": {"Access-Control-Allow-Origin": "*"},
    }