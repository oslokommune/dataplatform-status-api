import json
from aws_xray_sdk.core import patch_all, xray_recorder
from dataplatform.awslambda.logging import (
    logging_wrapper,
    log_add,
    log_exception,
)
from status.StatusData import StatusData
from status.common import response, response_error, is_owner

patch_all()


@logging_wrapper
@xray_recorder.capture("create_status")
def handler(event, context):
    db = StatusData()
    item = json.loads(event["body"])
    try:
        caller_is_owner = is_owner(event, item)
        log_add(is_owner=caller_is_owner)
        if not caller_is_owner:
            return response_error(403, "Access denied")

        trace_id = db.create_item(item)
        log_add(trace_id=trace_id)
        return response(200, json.dumps({"trace_id": trace_id}))
    except ValueError as ve:
        log_exception(ve)
        error_msg = f"Could not create status: {str(ve)}"
        return response_error(500, error_msg)
