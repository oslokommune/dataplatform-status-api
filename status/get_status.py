import simplejson
from aws_xray_sdk.core import patch_all, xray_recorder
from botocore.exceptions import ClientError
from okdata.aws.logging import (
    logging_wrapper,
    log_add,
    log_exception,
)

from status.common import (
    response,
    response_error,
    extract_dataset_id,
    extract_bearer_token,
)
from status.StatusData import StatusData
from okdata.resource_auth import ResourceAuthorizer

patch_all()
resource_authorizer = ResourceAuthorizer()


@logging_wrapper
@xray_recorder.capture("get_status")
def handler(event, context):
    params = event["pathParameters"]
    trace_id = params["trace_id"]
    log_add(trace_id=trace_id)
    db = StatusData()

    try:
        result = db.get_status(trace_id=trace_id)

        if result is None:
            error_msg = f"Could not find item: {trace_id}"
            return response_error(404, error_msg)

        status_items = result["Items"]
        dataset_id = extract_dataset_id(status_items[0])
        bearer_token = extract_bearer_token(event)
        log_add(dataset_id=dataset_id)
        if dataset_id and resource_authorizer.has_access(
            bearer_token,
            "okdata:dataset:write",
            f"okdata:dataset:{dataset_id}",
            use_whitelist=True,
        ):
            return response(200, simplejson.dumps(status_items))
        return response_error(403, "Access denied")

    except ClientError as ce:
        log_exception(ce)
        error_msg = f"Could not get status: {ce}"
        return response_error(404, error_msg)
