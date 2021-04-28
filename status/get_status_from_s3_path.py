import base64

import simplejson
from aws_xray_sdk.core import patch_all, xray_recorder
from botocore.exceptions import ClientError
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
    extract_bearer_token,
    extract_dataset_id,
)

patch_all()
resource_authorizer = ResourceAuthorizer()


@logging_wrapper
@xray_recorder.capture("get_status_from_s3_path")
def handler(event, context):
    params = event["pathParameters"]
    # The s3_path parameter MUST be base64 encoded since it can contain "/"
    # and any other character known to man.....
    path = base64.b64decode(params["s3_path"]).decode("utf-8", "ignore")
    log_add(s3_path=path)
    db = StatusData()

    try:
        status_item = db.get_status_from_s3_path(path)
        if status_item is None:
            error = "Could not find item"
            return response_error(404, error)

        dataset_id = extract_dataset_id(status_item)
        bearer_token = extract_bearer_token(event)
        log_add(trace_id=status_item["trace_id"], dataset_id=dataset_id)
        if dataset_id and resource_authorizer.has_access(
            bearer_token,
            "okdata:dataset:write",
            f"okdata:dataset:{dataset_id}",
            use_whitelist=True,
        ):
            ret = {
                # TODO: Return both id and trace_id until
                # all clients are updated
                "id": status_item["trace_id"],
                "trace_id": status_item["trace_id"],
            }
            return response(200, simplejson.dumps(ret))
        error = "Access denied"
        return response_error(403, error)

    except ClientError as ce:
        log_exception(ce)
        error_msg = f"Could not get status: {ce}"
        return response_error(404, error_msg)
