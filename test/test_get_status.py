from decimal import Decimal

from status import common
from status.get_status import handler
from status.StatusData import StatusData
from botocore.exceptions import ClientError

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
        mocker.patch.object(common, "_is_dataset_owner", return_value=True)
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

    def test_get_status_decimal_serialization(self, mocker):
        ret = {
            "Items": [
                {
                    "trace_event_status": "OK",
                    "operation": "lambda_invoker",
                    "component": "opening-hours",
                    "trace_status": "CONTINUE",
                    "meta": {
                        "git_rev": "get_exceptions_to_status_api:00f41d6",
                        "function_name": "opening-hours-dev-make-rules",
                        "function_version": "$LATEST",
                    },
                    "domain_id": "opening-hours/0.1.0",
                    "start_time": "2021-02-01T13:51:34.652891+00:00",
                    "trace_event_id": "3bb8b4ba-7952-4180-bd5b-6103f420e265",
                    "end_time": "2021-02-01T13:51:35.271952+00:00",
                    "duration": Decimal("618"),
                    "trace_id": "opening-hours-2becd3c3-0099-4e90-866e-6761c6d32242",
                    "domain": "dataset",
                },
            ]
        }
        mocker.patch.object(StatusData, "get_status", return_value=ret)
        mocker.patch.object(common, "_is_dataset_owner", return_value=True)

        result = handler(event, {})

        assert result["statusCode"] == 200

        body = json.loads(result["body"])

        assert len(body) == 1
        assert body[0]["duration"] == 618
