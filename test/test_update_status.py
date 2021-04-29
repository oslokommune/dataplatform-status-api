import json

from status.update_status import handler
from status.StatusData import StatusData
import test.test_data as test_data

event = {
    "pathParameters": {"trace_id": "uu-ii-dd"},
    "body": json.dumps({}),
    "headers": {"Authorization": f"bearer {test_data.bearer_token_with_access}"},
}
empty_context = {}


class TestUpdateStatus:
    def test_update_status_success(self, mocker, mock_auth):
        ret = {
            "Items": [
                {
                    "trace_id": "uu-ii-dd",
                    "trace_event_id": "first-id",
                    "domain": "dataset",
                    "domain_id": "ff",
                }
            ]
        }
        mocker.patch.object(StatusData, "get_status", return_value=ret)
        mocker.patch.object(
            StatusData,
            "update_status",
            return_value={"trace_id": "uu-ii-dd", "trace_event_id": "new-id"},
        )
        result = handler(event, empty_context)
        body = json.loads(result["body"])
        assert body["trace_event_id"] == "new-id"
        assert result["statusCode"] == 200

    def test_update_status_not_found(self, mocker):
        ret = None
        mocker.patch.object(StatusData, "get_status", return_value=ret)
        result = handler(event, empty_context)
        assert result["statusCode"] == 404
