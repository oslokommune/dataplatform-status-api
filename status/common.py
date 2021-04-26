import os

import requests
import simplejson

AUTHORIZER_API = os.environ["AUTHORIZER_API"]


def http_response(code, body):
    return {"statusCode": code, "body": body}


def response(code, body):
    return http_response(code, body)


def response_error(code, message):
    body = {"message": message}
    return http_response(code, simplejson.dumps(body))


def _is_dataset_owner(token, dataset_id):
    result = requests.get(
        f"{AUTHORIZER_API}/{dataset_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    result.raise_for_status()
    data = result.json()
    return data.get("access", False)


def is_owner(event, item):
    # TODO: Fallback to "domain" for backwards compatibility.
    # Expect "application" once clients are upadted.
    headers = event.get("headers")
    if headers:
        auth_header = event["headers"].get("Authorization", "")
        bearer_token = auth_header.split(" ")[-1]
        if item.get("application") == "dataset":
            dataset_id = item["application_id"]
            return _is_dataset_owner(bearer_token, dataset_id)

        if item["domain"] == "dataset":
            dataset_id = item["domain_id"].split("/")[0]
            return _is_dataset_owner(bearer_token, dataset_id)

    return False


def extract_bearer_token(event):
    auth_header = event["headers"].get("Authorization", "")
    return auth_header.split(" ")[-1]


def extract_dataset_id(status_item):
    if status_item.get("application") == "dataset":
        return status_item["application_id"]

    if status_item["domain"] == "dataset":
        return status_item["domain_id"].split("/")[0]
