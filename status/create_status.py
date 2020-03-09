import json
import logging
from status.StatusData import StatusData
from status.common import response, response_error, is_owner

log = logging.getLogger()
log.setLevel(logging.INFO)


def handler(event, context):
    db = StatusData()
    item = json.loads(event["body"])
    try:
        if is_owner(event, item) is False:
            log.info(f"User tried to create status but was denied: {item}")
            return response_error(403, "Access denied")

        generated_status_uuid = db.create_item(item)
        return response(200, json.dumps(generated_status_uuid))
    except ValueError as ve:
        log.info(f"ValueError: {ve} - from content: {item}")
        error = f"Could not create status: {str(ve)}"
        return response_error(500, error)
