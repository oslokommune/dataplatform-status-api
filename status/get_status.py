import json
import logging
from botocore.exceptions import ClientError
from status.common import response
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
            return response(404, json.dumps({"error": "Could not find item"}))
        else:
            return response(200, json.dumps(item["Items"]))

    except ClientError as ce:
        log.info(f"ClientError: {ce}")
        return response(404, json.dumps({"error": "Could not find item"}))
