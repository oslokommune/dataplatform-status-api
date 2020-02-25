from status.get_status import handler
from status.StatusData import StatusData
from botocore.exceptions import ClientError

import json

event = {"pathParameters": {"statusid": "uu-ii-dd"}}
empty_context = {}


class TestGetStatus:
    def test_get_status_success(self, mocker):
        ret = {
            "Items": [
                {"id": "uu-ii-dd", "event_id": "first-id"},
                {"id": "uu-ii-dd", "event_id": "second-id"},
            ]
        }
        mocker.patch.object(StatusData, "get_status", return_value=ret)
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
        assert "error" in body

    def test_get_status_failed_error(self, mocker):
        ret = "uu-ii-dd"
        mocked = mocker.patch.object(StatusData, "get_status", return_value=ret)
        mocked.side_effect = ClientError(
            operation_name="mocked", error_response={"Error": {}}
        )
        result = handler(event, empty_context)
        body = json.loads(result["body"])
        assert result["statusCode"] == 404
        assert "error" in body
