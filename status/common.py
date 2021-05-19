import os

import simplejson

AUTHORIZER_API = os.environ["AUTHORIZER_API"]


def http_response(code, body):
    return {"statusCode": code, "body": body}


def response(code, body):
    return http_response(code, body)


def response_error(code, message):
    body = {"message": message}
    return http_response(code, simplejson.dumps(body))


def extract_bearer_token(event):
    auth_header = event["headers"].get("Authorization", "")
    return auth_header.split(" ")[-1]


def extract_dataset_id(status_item):
    if status_item.get("application") == "dataset":
        return status_item["application_id"]

    if status_item["domain"] == "dataset":
        return status_item["domain_id"].split("/")[0]

    return None
