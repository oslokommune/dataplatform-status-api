import simplejson
from aws_xray_sdk.core import patch_all, xray_recorder
from okdata.aws.logging import (
    logging_wrapper,
    log_add,
    log_exception,
)
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
@xray_recorder.capture("create_status")
def handler(event, context):
    db = StatusData()
    status_item = simplejson.loads(event["body"])
    try:
        bearer_token = extract_bearer_token(event)
        dataset_id = extract_dataset_id(status_item)
        if not resource_authorizer.has_access(
            bearer_token,
            "okdata:dataset:write",
            f"okdata:dataset:{dataset_id}",
            use_whitelist=True,
        ):
            return response_error(403, "Access denied")

        trace_id = db.create_item(status_item)
        log_add(trace_id=trace_id)
        return response(200, simplejson.dumps({"trace_id": trace_id}))
    except ValueError as ve:
        log_exception(ve)
        error_msg = f"Could not create status: {str(ve)}"
        return response_error(500, error_msg)
