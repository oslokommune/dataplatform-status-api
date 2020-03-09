from status.update_status import handler
from status.StatusData import StatusData
from auth import SimpleAuth

import json

event = {
    "pathParameters": {"statusid": "uu-ii-dd"},
    "body": json.dumps({}),
    "headers": {"Authorization": ""},
}
empty_context = {}


class TestUpdateStatus:
    def test_update_status_success(self, mocker):
        ret = {
            "Items": [
                {
                    "id": "uu-ii-dd",
                    "event_id": "first-id",
                    "application": "dataset",
                    "application_id": "ff",
                }
            ]
        }
        mocker.patch.object(StatusData, "get_status", return_value=ret)
        mocker.patch.object(SimpleAuth, "is_owner", return_value=True)
        mocker.patch.object(
            StatusData,
            "update_status",
            return_value={"id": "uu-ii-dd", "event_id": "new-id"},
        )
        result = handler(event, empty_context)
        body = json.loads(result["body"])
        assert body["event_id"] == "new-id"
        assert result["statusCode"] == 200

    def test_update_status_not_found(self, mocker):
        ret = {"Items": []}
        mocker.patch.object(StatusData, "get_status", return_value=ret)
        result = handler(event, empty_context)
        assert result["statusCode"] == 404
