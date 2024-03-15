import json
import re
from unittest.mock import patch

import pytest
from okdata.aws.status import TraceStatus, TraceEventStatus
from okdata.aws.status.sdk import Status

from event.handler import act_on_queue


def _make_event(message):
    return {
        "Records": [
            {"EventSource": "aws:sns", "Sns": {"Message": json.dumps(message)}}
        ],
    }


def test_send_event_invalid_source():
    with pytest.raises(ValueError):
        act_on_queue({"Records": [{"EventSource": "unknown"}]}, None)


def test_send_empty_event():
    with pytest.raises(ValueError):
        act_on_queue({}, None)


def test_send_event_empty_message():
    assert not act_on_queue(_make_event({}), None)


def test_send_event_status_is_still_running():
    assert not act_on_queue(
        _make_event({"detail": {"status": "RUNNING"}}),
        None,
    )


def test_send_event_with_unknown_status():
    assert not act_on_queue(
        _make_event({"detail": {"status": "NOT_RECOGNIZED"}}),
        None,
    )


def test_send_event_with_succeeded_status(mocker):
    mocker.patch.object(Status, "done", return_value={})
    s = mocker.spy(Status, "add")

    trace_id = "trace-id-abc123-1a2b3c"
    with patch("event.handler.get_secret") as get_secret:
        get_secret.return_value = "abc123"
        assert act_on_queue(
            _make_event({"detail": {"status": "SUCCEEDED", "name": trace_id}}), None
        )
    assert (
        mocker.call(
            mocker.ANY,
            trace_id=trace_id,
            domain="dataset",
            operation="_set_finished_status",
            trace_event_status=TraceEventStatus.OK,
            trace_status=TraceStatus.FINISHED,
        )
        in s.call_args_list
    )
    Status.done.assert_called_once()


def test_send_event_with_aborted_status(mocker):
    mocker.patch.object(Status, "done", return_value={})
    s = mocker.spy(Status, "add")

    trace_id = "trace-id-abc123-1a2b3c"
    with patch("event.handler.get_secret") as get_secret:
        get_secret.return_value = "abc123"
        assert act_on_queue(
            _make_event({"detail": {"status": "ABORTED", "name": trace_id}}), None
        )
    assert (
        mocker.call(
            mocker.ANY,
            trace_id=trace_id,
            domain="dataset",
            operation="_set_finished_status",
            trace_event_status=TraceEventStatus.FAILED,
            trace_status=TraceStatus.FINISHED,
        )
        in s.call_args_list
    )
    Status.done.assert_called_once()


def test_send_event_with_unknown_trace_id(requests_mock):
    matcher = re.compile("status-api")
    requests_mock.register_uri("POST", matcher, status_code=404)

    trace_id = "trace-id-abc123-1a2b3c"
    with patch("event.handler.get_secret") as get_secret:
        get_secret.return_value = "abc123"
        assert not act_on_queue(
            _make_event({"detail": {"status": "SUCCEEDED", "name": trace_id}}), None
        )
