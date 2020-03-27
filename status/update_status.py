import json
from aws_xray_sdk.core import patch_all, xray_recorder
from dataplatform.awslambda.logging import logging_wrapper, log_add
from status.StatusData import StatusData
from status.common import response, response_error, is_owner

patch_all()


@logging_wrapper
@xray_recorder.capture("update_status")
def handler(event, context):
    params = event["pathParameters"]
    statusid = params["statusid"]
    log_add(status_id=statusid)

    content = json.loads(event["body"])

    db = StatusData()
    result = db.get_status(statusid)
    items = result["Items"]

    if len(items) != 0:
        caller_is_owner = is_owner(event, items[0])
        log_add(is_owner=caller_is_owner)
        if not caller_is_owner:
            return response_error(403, "Access denied")
        item = db.update_status(statusid, content)
        return response(200, json.dumps(item))
    error = f"Could not find the requested item to update: {statusid}"
    return response_error(404, error)
