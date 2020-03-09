import json
from auth import SimpleAuth


def http_response(code, body):
    return {"statusCode": code, "body": body}


def response(code, body):
    return http_response(code, body)


def response_error(code, message):
    body = {"message": message}
    return http_response(code, json.dumps(body))


def is_owner(event, item):
    if item["application"] == "dataset":
        dataset_id = item["application_id"]
        return SimpleAuth().is_owner(event, dataset_id)
    return False
