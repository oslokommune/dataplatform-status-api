import uuid
import boto3
from boto3.dynamodb.conditions import Key

from dataplatform.awslambda.logging import log_add


class StatusData:
    def __init__(self):
        dynamodb = boto3.resource("dynamodb", "eu-west-1")
        self.table = dynamodb.Table("dataplatform-status")

    def generate_uuid(self, dataset):
        new_uuid = uuid.uuid4()
        return f"{dataset}-{new_uuid}"[0:80]

    def generate_event_uuid(self):
        return str(uuid.uuid4())

    def create_item(self, body):
        body = self._remap_field_names(body)
        domain_id = body["domain_id"]
        trace_id = self.generate_uuid(domain_id)
        trace_event_id = self.generate_event_uuid()

        item = {
            "trace_id": trace_id,
            "trace_event_id": trace_event_id,
            "domain": body["domain"],
            "domain_id": domain_id,
            "component": body["component"],
            "user": body["user"],
            "start_time": body["start_time"],
            "end_time": body["end_time"],
            "trace_status": "STARTED",
            "trace_event_status": "OK",
        }

        if body.get("s3_path"):
            item["s3_path"] = body["s3_path"]
        if body.get("meta"):
            item["meta"] = body["meta"]
        if body.get("operation"):
            item["operation"] = body["operation"]
        if body.get("status_body"):
            item["status_body"] = body["status_body"]

        db_response = self.table.put_item(Item=item)

        if db_response["ResponseMetadata"]["HTTPStatusCode"] == 200:
            return trace_id
        else:
            raise ValueError(f"Was unable to create new status row for {domain_id}")

    def get_status(self, trace_id):
        response = self.table.query(KeyConditionExpression=Key("trace_id").eq(trace_id))
        if response["Items"]:
            return response
        else:
            return None

    def get_status_from_s3_path(self, path):
        response = self.table.query(
            IndexName="TraceIdByS3PathIndex",
            KeyConditionExpression=Key("s3_path").eq(path),
        )
        # There should never be more than 1 item with a single s3Path, so for now we only
        # return a value if this is true
        if len(response["Items"]) == 1:
            return response["Items"][0]
        return None

    def update_status(self, trace_id, body):
        body = self._remap_field_names(body)
        trace_event_id = self.generate_event_uuid()
        domain_id = body["domain_id"]

        update_item = {
            "trace_id": trace_id,
            "trace_event_id": trace_event_id,
            "domain": body["domain"],
            "domain_id": domain_id,
            "component": body["component"],
            "user": body["user"],
            "start_time": body["start_time"],
            "end_time": body["end_time"],
            "trace_status": body["trace_status"],
            "trace_event_status": body["trace_event_status"],
        }

        if body.get("s3_path"):
            update_item["s3_path"] = body["s3_path"]
        if body.get("meta"):
            update_item["meta"] = body["meta"]
        if body.get("operation"):
            update_item["operation"] = body["operation"]
        if body.get("status_body"):
            update_item["status_body"] = body["status_body"]

        db_response = self.table.put_item(Item=update_item)

        if db_response["ResponseMetadata"]["HTTPStatusCode"] == 200:
            return update_item
        else:
            raise ValueError(f"Was unable to update new status row for {trace_id}")

    def _remap_field_names(self, body):
        """
        Remap old field names to new naming for backward compatibility.
        TODO: Remove when all clients are updated.
        """
        field_map = {
            "id": "trace_id",
            "application": "domain",
            "application_id": "domain_id",
            "handler": "component",
            "run_status": "trace_status",
            "status": "trace_event_status",
            "body": "status_body",
            "s3path": "s3_path",
            "date_started": "start_time",
            "date_end": "end_time",
        }
        legacy_fields = list(set(body).intersection(field_map))
        log_add(remapped_legacy_fields=legacy_fields)
        return {
            field_map[field] if field in field_map else field: val
            for field, val in body.items()
        }
