import json

from okdata.aws.logging import log_add, logging_wrapper
from okdata.aws.status import TraceStatus, TraceEventStatus
from okdata.aws.status.sdk import Status
from okdata.aws.status.wrapper import _status_from_lambda_context

finished_statuses = {
    "ABORTED": TraceEventStatus.FAILED,
    "FAILED": TraceEventStatus.FAILED,
    "TIMED_OUT": TraceEventStatus.FAILED,
    "SUCCEEDED": TraceEventStatus.OK,
}


@logging_wrapper
def act_on_queue(event, context):
    records = event.get("Records")

    if not records:
        raise ValueError("Event does not contain Records")

    # We always get 1 event, see Reliability section of https://aws.amazon.com/sns/faqs/
    record = records[0]
    source = record["EventSource"]

    if source != "aws:sns":
        raise ValueError(
            f"Unsuported 'EventSource' {source}. Supported types: 'aws:sns'"
        )

    event = json.loads(record["Sns"]["Message"])

    try:
        event_status = event["detail"]["status"]
    except KeyError:
        return False

    trace_id = event["detail"].get("name")
    log_add(trace_id=trace_id, event_status=event_status)

    # Ignore statuses where pipeline is not finished
    if event_status not in finished_statuses:
        return False

    return _set_finished_status(event, context, trace_id, event_status)


def _set_finished_status(event, context, trace_id, event_status):
    status = Status(_status_from_lambda_context(event, context))

    trace_event_status = finished_statuses[event_status]
    log_add(trace_event_status=trace_event_status)

    status.add(
        trace_id=trace_id,
        domain="dataset",
        operation="_set_finished_status",
        trace_event_status=trace_event_status,
        trace_status=TraceStatus.FINISHED,
    )

    status_api_ok = status.done() is not None
    log_add(status_api_ok=status_api_ok)

    return status_api_ok
