from status.get_status_from_s3_path import handler
from status.StatusData import StatusData
from auth import SimpleAuth
import json

# s3path: echo -n "my/path/to/file (2020).xlsx" | base64
event = {"pathParameters": {"s3path": "bXkvcGF0aC90by9maWxlICgyMDIwKS54bHN4"}}
empty_context = {}


class TestGetStatusFromS3Path:
    def test_get_path_as_owner(self, mocker):
        ret = {
            "id": "my-status-id",
            "application": "dataset",
            "application_id": "my-dataset",
        }
        mocker.patch.object(StatusData, "get_status_from_s3_path", return_value=ret)
        mocker.patch.object(SimpleAuth, "is_owner", return_value=True)
        result = handler(event, empty_context)
        body = json.loads(result["body"])
        assert body["id"] == "my-status-id"
        assert result["statusCode"] == 200

    def test_when_user_is_not_owner(self, mocker):
        ret = {
            "id": "my-status-id",
            "application": "event",
            "application_id": "my-dataset",
        }
        mocker.patch.object(StatusData, "get_status_from_s3_path", return_value=ret)
        mocker.patch.object(SimpleAuth, "is_owner", return_value=False)
        result = handler(event, empty_context)
        body = json.loads(result["body"])
        assert "message" in body
        assert result["statusCode"] == 403

    def test_owner_when_application_is_not_dataset(self, mocker):
        ret = {
            "id": "my-status-id",
            "application": "event",
            "application_id": "my-dataset",
        }
        mocker.patch.object(StatusData, "get_status_from_s3_path", return_value=ret)
        result = handler(event, empty_context)
        body = json.loads(result["body"])
        assert "message" in body
        assert result["statusCode"] == 403

    def test_when_path_is_not_found(self, mocker):
        ret = None
        mocker.patch.object(StatusData, "get_status_from_s3_path", return_value=ret)
        result = handler(event, empty_context)
        body = json.loads(result["body"])
        assert "message" in body
        assert result["statusCode"] == 404
