import json
import logging
from status.StatusData import StatusData
from status.common import response

log = logging.getLogger()
log.setLevel(logging.INFO)


def handler(event, context):
    db = StatusData()
    content = json.loads(event["body"])
    try:
        generated_status_uuid = db.create_item(content)
        return response(200, json.dumps(generated_status_uuid))
    except ValueError as ve:
        log.info(ve)
        return response(500, str(ve))
