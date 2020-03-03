from status.create_status import handler
from status.StatusData import StatusData
import json

event = {"body": json.dumps({})}
empty_context = {}


class TestCreateStatus:
    def test_create_status_success(self, mocker):
        ret = "uu-ii-dd"
        mocker.patch.object(StatusData, "create_item", return_value=ret)
        result = handler(event, empty_context)
        body = json.loads(result["body"])
        assert body == ret
        assert result["statusCode"] == 200

    def test_create_status_failed_error(self, mocker):
        ret = "uu-ii-dd"
        mocked = mocker.patch.object(StatusData, "create_item", return_value=ret)
        mocked.side_effect = ValueError("errorMessage")
        result = handler(event, empty_context)
        body = json.loads(result["body"])
        assert result["statusCode"] == 500
        assert body["message"] == "Could not create status: errorMessage"
