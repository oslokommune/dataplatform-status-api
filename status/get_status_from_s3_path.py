import base64

import simplejson
from aws_xray_sdk.core import patch_all, xray_recorder
from botocore.exceptions import ClientError
from okdata.aws.logging import (
    logging_wrapper,
    log_add,
    log_exception,
)

from status.StatusData import StatusData
from status.common import response, response_error, is_owner

patch_all()


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
        item = db.get_status_from_s3_path(path)
        if item is None:
            error = "Could not find item"
            return response_error(404, error)

        caller_is_owner = is_owner(event, item)
        log_add(trace_id=item["trace_id"], is_owner=caller_is_owner)
        if is_owner(event, item):
            ret = {
                # TODO: Return both id and trace_id until
                # all clients are updated
                "id": item["trace_id"],
                "trace_id": item["trace_id"],
            }
            return response(200, simplejson.dumps(ret))
        error = "Access denied"
        return response_error(403, error)

    except ClientError as ce:
        log_exception(ce)
        error_msg = f"Could not get status: {ce}"
        return response_error(404, error_msg)
