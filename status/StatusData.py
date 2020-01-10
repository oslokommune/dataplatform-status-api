import boto3
from botocore.exceptions import ClientError

import logging
import json
import datetime
import uuid

log = logging.getLogger()


class StatusData:
    def __init__(self):
        dynamodb = boto3.resource("dynamodb", "eu-west-1")
        self.table = dynamodb.Table("status_data")

    def generate_uuid(self, dataset):
        new_uuid = uuid.uuid4()
        return f"{dataset}-{new_uuid}"[0:80]

    def create_item(self, body):
        dataset_id = body["dataset-id"]
        status_row_id = self.generate_uuid(dataset_id)
        application = body["application"]
        user = body["user"]
        date_started = body["date_started"]
        date_end = body["date_end"]
        run_status = 'STARTED'
        status = 'OK'
        status_body = body["body"]

        db_response = self.table.put_item(
            Item={
                "id": status_row_id,
                "application": application,
                "user": user,
                "date_started": date_started,
                "date_end": date_end,
                "run_status": run_status,
                "status": status,
                "status_body": status_body,
                "dataset_id": dataset_id
            }
        )

        if db_response["ResponseMetadata"]["HTTPStatusCode"] == 200:
            return status_row_id
        else:
            raise ValueError(
                f"Was unable to create new status row for {dataset_id}")

    def get_status(self, id):
        key = {"id": id}
        db_response = self.table.get_item(Key=key)
        return db_response

    def update_status(self, id, body):
        log.info(f"BODY RECEIVED: {body}")
        dataset_id = body["dataset-id"]
        status_row_id = id
        application = body["application"]
        user = body["user"]
        date_started = body["date_started"]
        date_end = body["date_end"]
        run_status = body["run_status"]
        status = body["status"]
        status_body = body["body"]

        db_response = self.table.put_item(
            Item={
                "id": status_row_id,
                "application": application,
                "user": user,
                "date_started": date_started,
                "date_end": date_end,
                "run_status": run_status,
                "status": status,
                "status_body": status_body,
                "dataset_id": dataset_id
            }
        )

        if db_response["ResponseMetadata"]["HTTPStatusCode"] == 200:
            return db_response
        else:
            raise ValueError(
                f"Was unable to update new status row for {dataset_id}")
