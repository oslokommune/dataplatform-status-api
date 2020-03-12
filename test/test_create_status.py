from status.create_status import handler
from status.StatusData import StatusData
from auth import SimpleAuth
import json

event = {
    "body": json.dumps({"application": "dataset", "application_id": "my-uu-ii-dds"}),
    "headers": {"Authorization": ""},
}
event_wrong_application = {
    "body": json.dumps({"application": "foobar", "application_id": "my-uu-ii-dds"}),
    "headers": {"Authorization": ""},
}
empty_context = {}


class TestCreateStatus:
    def test_create_status_success(self, mocker):
        ret = "uu-ii-dd"
        mocker.patch.object(StatusData, "create_item", return_value=ret)
        mocker.patch.object(SimpleAuth, "is_owner", return_value=True)
        result = handler(event, empty_context)
        body = json.loads(result["body"])
        assert body == ret
        assert result["statusCode"] == 200

    def test_create_status_failed_error(self, mocker):
        ret = "uu-ii-dd"
        mocked = mocker.patch.object(StatusData, "create_item", return_value=ret)
        mocker.patch.object(SimpleAuth, "is_owner", return_value=True)
        mocked.side_effect = ValueError("errorMessage")
        result = handler(event, empty_context)
        body = json.loads(result["body"])
        assert result["statusCode"] == 500
        assert body["message"] == "Could not create status: errorMessage"

    def test_create_status_application_is_not_dataset(self, mocker):
        ret = "uu-ii-dd"
        mocked = mocker.patch.object(StatusData, "create_item", return_value=ret)
        mocker.patch.object(SimpleAuth, "is_owner", return_value=True)
        mocked.side_effect = ValueError("errorMessage")
        result = handler(event_wrong_application, empty_context)
        body = json.loads(result["body"])
        assert result["statusCode"] == 403
        assert body["message"] == "Access denied"