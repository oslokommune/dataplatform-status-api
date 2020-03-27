import json
from aws_xray_sdk.core import patch_all, xray_recorder
from dataplatform.awslambda.logging import (
    logging_wrapper,
    log_add,
    log_exception,
)
from botocore.exceptions import ClientError
from status.common import response, response_error, is_owner
from status.StatusData import StatusData

patch_all()


@logging_wrapper
@xray_recorder.capture("get_status")
def handler(event, context):
    params = event["pathParameters"]
    statusid = params["statusid"]
    log_add(status_id=statusid)
    db = StatusData()

    try:
        item = db.get_status(id=statusid)

        if item is None:
            error_msg = f"Could not find item: {statusid}"
            return response_error(404, error_msg)

        items = item["Items"]
        caller_is_owner = is_owner(event, items[0])
        log_add(is_owner=caller_is_owner)
        if not caller_is_owner:
            return response_error(403, "Access denied")
        return response(200, json.dumps(items))

    except ClientError as ce:
        log_exception(ce)
        error_msg = f"Could not get status: {ce}"
        return response_error(404, error_msg)
