import uuid
import boto3
from boto3.dynamodb.conditions import Key

from okdata.aws.logging import log_add


class StatusData:
    def __init__(self):
        dynamodb = boto3.resource("dynamodb", "eu-west-1")
        self.table = dynamodb.Table("dataplatform-status")

    def generate_uuid(self, dataset_id):
        new_uuid = uuid.uuid4()
        return f"{dataset_id}-{new_uuid}"[0:80]

    def generate_event_uuid(self):
        return str(uuid.uuid4())

    def create_item(self, body):
        body = self._remap_field_names(body)
        domain_id = body["domain_id"]
        dataset_id = domain_id.split("/")[0]
        trace_id = self.generate_uuid(dataset_id)
        trace_event_id = self.generate_event_uuid()

        item = {
            "trace_id": trace_id,
            "trace_event_id": trace_event_id,
            "domain": body["domain"],
            "domain_id": domain_id,
            "start_time": body["start_time"],
            "end_time": body["end_time"],
            "component": body["component"],
            "trace_status": "STARTED",
            "trace_event_status": "OK",
        }

        optional = ["operation", "user", "s3_path", "status_body", "meta"]
        for field_name in optional:
            if field_name in body:
                item[field_name] = body[field_name]

        db_response = self.table.put_item(Item=item)

        if db_response["ResponseMetadata"]["HTTPStatusCode"] == 200:
            return trace_id
        else:
            raise ValueError(f"Unable to create new trace for {domain_id}")

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

        update_item = {
            "trace_id": trace_id,
            "trace_event_id": trace_event_id,
            "domain": body["domain"],
            "component": body["component"],
            "start_time": body["start_time"],
            "end_time": body["end_time"],
            "trace_status": body["trace_status"],
            "trace_event_status": body["trace_event_status"],
        }

        optional = ["domain_id", "operation", "user", "s3_path", "status_body", "meta"]
        for field_name in optional:
            if field_name in body:
                update_item[field_name] = body[field_name]

        db_response = self.table.put_item(Item=update_item)

        if db_response["ResponseMetadata"]["HTTPStatusCode"] == 200:
            return update_item
        else:
            raise ValueError(f"Unable to update status for trace {trace_id}")

    def _remap_field_names(self, body):
        """
        Remap old field names to new naming for backward compatibility.
        TODO: Remove when all clients are updated.
        """
        field_map = {
            "id": "trace_id",
            "application": "domain",
            "application_id": "domain_id",
            "date_started": "start_time",
            "date_end": "end_time",
            "handler": "component",
            "run_status": "trace_status",
            "status": "trace_event_status",
            "s3path": "s3_path",
            "body": "status_body",
        }
        legacy_fields = list(set(body).intersection(field_map))
        log_add(remapped_legacy_fields=legacy_fields)
        return {
            field_map[field] if field in field_map else field: val
            for field, val in body.items()
        }
