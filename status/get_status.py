import json
import logging
from botocore.exceptions import ClientError
from status.common import response, response_error
from status.StatusData import StatusData

log = logging.getLogger()
log.setLevel(logging.INFO)


def handler(event, context):
    params = event["pathParameters"]
    statusid = params["statusid"]
    db = StatusData()

    try:
        item = db.get_status(id=statusid)

        if item is None:
            error = {"message": f"Could not find item: {statusid}"}
            return response_error(404, json.dumps(error))
        else:
            return response(200, json.dumps(item["Items"]))

    except ClientError as ce:
        log.info(f"ClientError: {ce}")
        error = {"message": f"Could not get status: {ce}"}
        return response_error(404, json.dumps(error))
