import json

from status.get_status_from_s3_path import handler
from status.StatusData import StatusData
import test.test_data as test_data

# s3path: echo -n "my/path/to/file (2020).xlsx" | base64
event = {
    "headers": {"Authorization": f"bearer {test_data.bearer_token_with_access}"},
    "pathParameters": {"s3_path": "bXkvcGF0aC90by9maWxlICgyMDIwKS54bHN4"},
}
empty_context = {}


class TestGetStatusFromS3Path:
    def test_get_path_as_owner(self, mocker, mock_auth):
        ret = {
            "trace_id": "my-status-id",
            "domain": "dataset",
            "domain_id": "my-dataset",
        }
        mocker.patch.object(StatusData, "get_status_from_s3_path", return_value=ret)
        result = handler(event, empty_context)
        body = json.loads(result["body"])
        assert body["id"] == "my-status-id"
        assert body["trace_id"] == "my-status-id"
        assert result["statusCode"] == 200

    def test_when_user_is_not_owner(self, mocker, mock_auth):
        ret = {
            "trace_id": "my-status-id",
            "domain": "event",
            "domain_id": "my-dataset",
        }
        mocker.patch.object(StatusData, "get_status_from_s3_path", return_value=ret)
        result = handler(event, empty_context)
        body = json.loads(result["body"])
        assert "message" in body
        assert result["statusCode"] == 403

    def test_owner_when_domain_is_not_dataset(self, mocker, mock_auth):
        ret = {
            "trace_id": "my-status-id",
            "domain": "event",
            "domain_id": "my-dataset",
        }
        mocker.patch.object(StatusData, "get_status_from_s3_path", return_value=ret)
        result = handler(event, empty_context)
        body = json.loads(result["body"])
        assert "message" in body
        assert result["statusCode"] == 403

    def test_when_path_is_not_found(self, mocker, mock_auth):
        ret = None
        mocker.patch.object(StatusData, "get_status_from_s3_path", return_value=ret)
        result = handler(event, empty_context)
        body = json.loads(result["body"])
        assert "message" in body
        assert result["statusCode"] == 404
