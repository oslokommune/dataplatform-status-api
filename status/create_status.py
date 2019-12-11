import json
import logging
from status.StatusData import StatusData

log = logging.getLogger()
log.setLevel(logging.INFO)


def handler(event, context):
    params = event["pathParameters"]
    uuid = params["uuid"]
    db = StatusData()
    db_response = db.create_item(id=uuid)
    status_code = db_response["ResponseMetadata"]["HTTPStatusCode"]

    if status_code is not 200:
        return response(500, json.dumps({"error": "Could not create item"}))
    else:
        return response(200, json.dumps(db_response))


def response(code, body):
    return {
        "statusCode": code,
        "body": body,
        "headers": {"Access-Control-Allow-Origin": "*"},
    }
