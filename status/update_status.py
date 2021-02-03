import simplejson
from aws_xray_sdk.core import patch_all, xray_recorder
from okdata.aws.logging import logging_wrapper, log_add

from status.StatusData import StatusData
from status.common import response, response_error, is_owner

patch_all()


@logging_wrapper
@xray_recorder.capture("update_status")
def handler(event, context):
    params = event["pathParameters"]
    trace_id = params["trace_id"]
    log_add(trace_id=trace_id)

    content = simplejson.loads(event["body"])

    db = StatusData()
    result = db.get_status(trace_id)

    if result is None:
        error = f"Could not find the requested item to update: {trace_id}"
        return response_error(404, error)

    items = result["Items"]
    caller_is_owner = is_owner(event, items[0])
    log_add(is_owner=caller_is_owner)
    if not caller_is_owner:
        return response_error(403, "Access denied")
    item = db.update_status(trace_id, content)
    return response(200, simplejson.dumps(item))
