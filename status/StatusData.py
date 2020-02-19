import boto3
from boto3.dynamodb.conditions import Key, Attr
import logging
import uuid

log = logging.getLogger()


class StatusData:
    def __init__(self):
        dynamodb = boto3.resource("dynamodb", "eu-west-1")
        self.table = dynamodb.Table("status-api-data")

    def generate_uuid(self, dataset):
        new_uuid = uuid.uuid4()
        return f"{dataset}-{new_uuid}"[0:80]

    def generate_event_uuid(self):
        return str(uuid.uuid4())

    def create_item(self, body):
        application = body["application"]
        application_id = body["application_id"]
        handler = body["handler"]
        status_row_id = self.generate_uuid(application_id)
        event_id = self.generate_event_uuid()

        user = body["user"]
        date_started = body["date_started"]
        date_end = body["date_end"]
        run_status = "STARTED"
        status = "OK"
        status_body = body["body"]
        s3path = "N/A"
        if "s3path" in body:
            s3path = body["s3path"]

        db_response = self.table.put_item(
            Item={
                "id": status_row_id,
                "event_id": event_id,
                "application": application,
                "user": user,
                "date_started": date_started,
                "date_end": date_end,
                "run_status": run_status,
                "status": status,
                "status_body": status_body,
                "application_id": application_id,
                "handler": handler,
                "s3_path": s3path,
            }
        )

        if db_response["ResponseMetadata"]["HTTPStatusCode"] == 200:
            return status_row_id
        else:
            raise ValueError(
                f"Was unable to create new status row for {application_id}"
            )

    def get_status(self, id):
        response = self.table.query(KeyConditionExpression=Key("id").eq(id))
        if response["Items"]:
            return response
        else:
            return None

    def get_status_from_s3_path(self, path):
        resp = self.table.scan(FilterExpression=Attr("s3path").eq(path))
        # There should never be more than 1 item with a single s3Path, so for now we only
        # return a value if this is true
        if len(resp["Items"]) == 1:
            return resp["Items"][0]
        return None

    def update_status(self, id, body):
        event_id = self.generate_event_uuid()
        status_row_id = id
        application = body["application"]
        application_id = body["application_id"]
        handler = body["handler"]
        user = body["user"]
        date_started = body["date_started"]
        date_end = body["date_end"]
        run_status = body["run_status"]
        status = body["status"]
        status_body = body["body"]
        s3path = body["s3path"]

        update_item = {
            "id": status_row_id,
            "event_id": event_id,
            "application": application,
            "application_id": application_id,
            "handler": handler,
            "user": user,
            "date_started": date_started,
            "date_end": date_end,
            "run_status": run_status,
            "status": status,
            "status_body": status_body,
            "s3_path": s3path,
        }

        db_response = self.table.put_item(Item=update_item)

        if db_response["ResponseMetadata"]["HTTPStatusCode"] == 200:
            return update_item
        else:
            raise ValueError(
                f"Was unable to update new status row for {application_id}"
            )
