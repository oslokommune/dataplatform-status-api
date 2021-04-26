import simplejson
from aws_xray_sdk.core import patch_all, xray_recorder
from okdata.aws.logging import logging_wrapper, log_add
from okdata.resource_auth import ResourceAuthorizer

from status.StatusData import StatusData
from status.common import (
    response,
    response_error,
    extract_dataset_id,
    extract_bearer_token,
)

patch_all()
resource_authorizer = ResourceAuthorizer()


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

    status_items = result["Items"]
    dataset_id = extract_dataset_id(status_items[0])
    bearer_token = extract_bearer_token(event)

    if not resource_authorizer.has_access(
        bearer_token,
        "okdata:dataset:write",
        f"okdata:dataset:{dataset_id}",
        use_whitelist=True,
    ):
        return response_error(403, "Access denied")
    item = db.update_status(trace_id, content)
    return response(200, simplejson.dumps(item))
