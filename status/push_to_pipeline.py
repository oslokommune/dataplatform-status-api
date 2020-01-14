import json
import logging
from status.StatusData import StatusData

log = logging.getLogger()
log.setLevel(logging.INFO)


def handler(event, context):
    db = StatusData()
    content = json.loads(event["body"])
    try:
        sns_response = db.push_to_pipeline(content)
        return response(200, json.dumps(sns_response))
    except Exception as e:
        log.info(e)
        return response(500, e)


def response(code, body):
    return {
        "statusCode": code,
        "body": body,
        "headers": {"Access-Control-Allow-Origin": "*"},
    }
