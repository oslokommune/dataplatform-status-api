import boto3
import re
import json
import pytest
from moto import mock_dynamodb2
from status.StatusData import StatusData

event = {"pathParameters": {"statusid": "uu-ii-dd"}, "body": json.dumps({})}
empty_context = {}


@pytest.fixture()
def dynamodb():
    with mock_dynamodb2():
        yield boto3.resource("dynamodb", "eu-west-1")


@pytest.fixture(autouse=True)
def status_table(dynamodb):
    return create_table(dynamodb)


def create_table(dynamodb):
    table_name = "status-api-data"
    hashkey = "id"

    keyschema = [{"AttributeName": hashkey, "KeyType": "HASH"}]
    attributes = [{"AttributeName": hashkey, "AttributeType": "S"}]
    gsis = []

    return dynamodb.create_table(
        TableName=table_name,
        KeySchema=keyschema,
        AttributeDefinitions=attributes,
        ProvisionedThroughput={"ReadCapacityUnits": 5, "WriteCapacityUnits": 5},
        GlobalSecondaryIndexes=gsis,
    )


status_body = {
    "application": "my-app",
    "application_id": "my-app-id",
    "handler": "my-handler",
    "user": "user",
    "date_started": "2020",
    "date_end": "2021",
    "body": {},
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
        statusid = s.create_item(status_body)
        result = s.get_status(statusid)
        assert result["Items"][0]["id"] == statusid

    def test_get_status_not_found(self, dynamodb, status_table):
        s = StatusData()
        statusid = "my-id"
        result = s.get_status(statusid)
        assert result is None

    def test_get_status_from_s3_path(self, dynamodb, status_table):
        s = StatusData()
        s.create_item(status_body)
        result = s.get_status_from_s3_path("/my/path")
        matcher = re.compile("my-app-id-")
        assert matcher.match(result["id"])

    def test_get_status_from_s3_path_not_found(self, dynamodb, status_table):
        s = StatusData()
        result = s.get_status_from_s3_path("/my/non/existing/path")
        assert result is None

    def test_update_status(self, dynamodb, status_table):
        s = StatusData()
        result = s.update_status("my-id", status_body)
        assert result["id"] == "my-id"
        assert result["application_id"] == "my-app-id"
