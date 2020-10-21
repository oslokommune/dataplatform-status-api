import boto3
import re
import json
import pytest
from moto import mock_dynamodb2
from status.StatusData import StatusData

event = {"pathParameters": {"trace_id": "uu-ii-dd"}, "body": json.dumps({})}
empty_context = {}


@pytest.fixture()
def dynamodb():
    with mock_dynamodb2():
        yield boto3.resource("dynamodb", "eu-west-1")


@pytest.fixture(autouse=True)
def status_table(dynamodb):
    return create_table(dynamodb)


def create_table(dynamodb):
    table_name = "dataplatform-status"
    hashkey = "trace_id"

    keyschema = [{"AttributeName": hashkey, "KeyType": "HASH"}]
    attributes = [
        {"AttributeName": hashkey, "AttributeType": "S"},
        {"AttributeName": "s3_path", "AttributeType": "S"},
    ]
    gsis = [
        {
            "IndexName": "TraceIdByS3PathIndex",
            "KeySchema": [{"AttributeName": "s3_path", "KeyType": "HASH"}],
            "Projection": {"ProjectionType": "ALL"},
        }
    ]

    return dynamodb.create_table(
        TableName=table_name,
        KeySchema=keyschema,
        AttributeDefinitions=attributes,
        ProvisionedThroughput={"ReadCapacityUnits": 5, "WriteCapacityUnits": 5},
        GlobalSecondaryIndexes=gsis,
    )


status_body = {
    "domain": "my-app",
    "domain_id": "my-app-id",
    "component": "my-component",
    "user": "user",
    "start_time": "2020",
    "end_time": "2021",
    "status_body": {"relevant": "data"},
    "s3_path": "/my/path",
    "trace_status": "OK",
    "event_status": "STARTED",
}
status_body_legacy = {
    "application": "my-app",
    "application_id": "my-app-id",
    "handler": "my-component",
    "user": "user",
    "date_started": "2020",
    "date_end": "2021",
    "body": {"relevant": "data"},
    "s3path": "/my/path",
    "run_status": "OK",
    "status": "STARTED",
}


class TestStatusData:
    def test_generate_uuid(self):
        matcher = re.compile("my-dataset-")
        s = StatusData()
        uuid = s.generate_uuid("my-dataset")
        assert matcher.match(uuid)

    def test_generate_event_uuid(self):
        s = StatusData()
        uuid = s.generate_event_uuid()
        assert len(uuid) == 36

    def test_create_item(self, dynamodb, status_table):
        s = StatusData()
        result = s.create_item(status_body)
        matcher = re.compile("my-app-id-")
        assert matcher.match(result)

    def test_get_status(self, dynamodb, status_table):
        s = StatusData()
        trace_id = s.create_item(status_body)
        result = s.get_status(trace_id)
        assert result["Items"][0]["trace_id"] == trace_id

    def test_get_status_not_found(self, dynamodb, status_table):
        s = StatusData()
        trace_id = "my-id"
        result = s.get_status(trace_id)
        assert result is None

    def test_get_status_from_s3_path(self, dynamodb, status_table):
        s = StatusData()
        s.create_item(status_body)
        result = s.get_status_from_s3_path("/my/path")
        matcher = re.compile("my-app-id-")
        assert matcher.match(result["trace_id"])

    def test_get_status_from_s3_path_not_found(self, dynamodb, status_table):
        s = StatusData()
        result = s.get_status_from_s3_path("/my/non/existing/path")
        assert result is None

    def test_update_status(self, dynamodb, status_table):
        s = StatusData()
        result = s.update_status("my-id", status_body)
        assert result["trace_id"] == "my-id"
        assert result["domain_id"] == "my-app-id"

    def test_update_status_legacy_field_names(self, dynamodb, status_table):
        s = StatusData()
        result = s.update_status("my-id", status_body_legacy)
        assert result["trace_id"] == "my-id"
        assert result["domain"] == status_body_legacy["application"]
        assert result["domain_id"] == status_body_legacy["application_id"]
        assert result["component"] == status_body_legacy["handler"]
        assert result["trace_status"] == status_body_legacy["run_status"]
        assert result["event_status"] == status_body_legacy["status"]
        assert result["status_body"] == status_body_legacy["body"]
        assert result["s3_path"] == status_body_legacy["s3path"]
        assert result["start_time"] == status_body_legacy["date_started"]
        assert result["end_time"] == status_body_legacy["date_end"]
