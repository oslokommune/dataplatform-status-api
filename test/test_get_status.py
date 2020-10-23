from status.get_status import handler
from status.StatusData import StatusData
from botocore.exceptions import ClientError
from auth import SimpleAuth

import json

event = {"headers": {"Authorization": ""}, "pathParameters": {"trace_id": "uu-ii-dd"}}
empty_context = {}


class TestGetStatus:
    def test_get_status_success(self, mocker):
        ret = {
            "Items": [
                {
                    "trace_id": "uu-ii-dd",
                    "trace_event_id": "first-id",
                    "domain": "dataset",
                    "domain_id": "foo",
                },
                {
                    "trace_id": "uu-ii-dd",
                    "trace_event_id": "second-id",
                    "domain": "dataset",
                    "domain_id": "bar",
                },
            ]
        }
        mocker.patch.object(StatusData, "get_status", return_value=ret)
        mocker.patch.object(SimpleAuth, "is_owner", return_value=True)
        result = handler(event, empty_context)
        body = json.loads(result["body"])
        assert len(body) == 2
        assert result["statusCode"] == 200

    def test_get_status_not_found(self, mocker):
        ret = None
        mocker.patch.object(StatusData, "get_status", return_value=ret)
        result = handler(event, empty_context)
        body = json.loads(result["body"])
        assert result["statusCode"] == 404
        assert "message" in body

    def test_get_status_failed_error(self, mocker):
        ret = "uu-ii-dd"
        mocked = mocker.patch.object(StatusData, "get_status", return_value=ret)
        mocked.side_effect = ClientError(
            operation_name="mocked", error_response={"Error": {}}
        )
        result = handler(event, empty_context)
        body = json.loads(result["body"])
        assert result["statusCode"] == 404
        assert "message" in body
