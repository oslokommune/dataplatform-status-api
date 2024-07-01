# status-api
API for tracking status through an asynchronous system.

## Deploy

Deploy to both dev and prod is automatic via GitHub Actions on push to
`main`. You can alternatively deploy from local machine with: `make deploy` or
`make deploy-prod`.

## Install/Setup
1. Install [Serverless Framework](https://serverless.com/framework/docs/getting-started/)
2. Setup venv
```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
3. Install Serverless plugins: `make init`
4. Install Python toolchain: `python3 -m pip install (--user) tox black pip-tools`
   - If running with `--user` flag, add `$HOME/.local/bin` to `$PATH`

# Status architecture
The status API defines a set of API endpoints to track events through a system
from start to end. Initially created to track the execution state of an
asynchronous state machine in AWS, it can be used for any task that needs to
track the status from start to end: both synchronous and asynchronous
executions.

**Example**: *As a user I want to upload a file to a dataset I own. To ensure
that the data has been processed, I need to know if the pipeline has executed
successfully. Since the pipeline is asynchronous I don't get immediate feedback
after uploading the file, I want to be able to query the system for the
data-processing status*.

The pseudo-code for the use-case is:

* **user -> upload file**
  * `trace_id` = return value from upload process
* **user -> query status API by trace ID**
  * Repeat query until state (`trace_status`) is `FINISHED`
* **user -> check if successful**
  * If `trace_event_status` is `FAILED` -> get a list of what has been done
    within the pipeline and the reason for failing
  * If `trace_event_status` is `OK` -> continue with processing other data that
    relies on data processed in the above steps

Each Lambda function (see below) or step in the execution stage is responsible
for setting the correct status for each step.

## Data lineage
The status API provides the status of an execution throughout a system, but it
also has the added benefit that data lineage can be traced through the system at
the same time. When using the `status_wrapper` from
[okdata-aws](https://github.com/oslokommune/okdata-aws) (or setting them
manually using the `Status` class), you can generate trace events and include
relevant data, e.g. which files was processed in each step, and what was the
result of the data going out of each step in the function.

## Database structure
Database is setup in
[dataplatform-config](https://github.com/oslokommune/dataplatform-config/tree/main/devops/modules/services/status-api).

The main fields in the database:

| Field              | Type           | Description                                                                                           | Example                                          |
| -----------        | -------------- | -----------                                                                                           | -----------                                      |
| trace_id           | string         | The ID used to trace connected events throughout the system (N-entries). ***Primary partition key***. | `my-dataset-uu-ii-dd`                            |
| trace_event_id     | uuid           | Unique ID per event (many `trace_event_id` per `trace_id`).                                           | `uu-ii-dd`                                       |
| domain             | string         | The domain that this status pertains to, e.g. `dataset` for publishing data or events to a dataset    | `dataset`                                        |
| domain_id          | string         | A domain specific ID to be able to look up the owner or source. Includes version number.              | `dataset.name/version`                           |
| start_time         | time           | Start of execution. ***Primary sort key***.                                                           | `2020-03-02T12:34:23.042400`                     |
| end_time           | time           | End of execution                                                                                      | `2020-03-02T12:34:24.042400`                     |
| trace_status       | string         | Overall status for the trace ID.                                                                      | `CONTINUE`, `FINISHED`                           |
| trace_event_status | string         | Status for the `trace_event_id`.                                                                      | `OK`, `FAILED`                                   |
| user               | string         | The user that is used in `handler` to execute the event                                               | `service-user-s3-writer`, `ooo123456`            |
| component          | string         | The component that is the source of the event.                                                        | `data-uploader`, `s3-writer`                     |
| operation          | string         | The operation (e.g. method) performed by the component, e.g. Lambda function name                     | `copy`                                           |
| status_body        | object         | Namespace where the component can add data relevant for the execution.                                | `{"files_incoming": [], "files_outgoing": []}`   |
| meta               | object         | Metadata about the execution, such as Git revision of the component.                                  | `{"git_rev": ...}`                               |
| s3_path            | string         | Path of the uploaded file.                                                                            | `raw/yellow/my-dataset/version/edition/file.xls` |
| duration           | number         | Duration of execution in milliseconds.                                                                | `123`                                            |
| exception          | object         | Details of exception that has occurred.                                                               | `ZeroDivisionError: division by zero`            |
| errors             | object         | Error messages to be read by the end user.                                                            | `[{"message": {"nb": "", "en": ""}, ...]`        |

**Note**: While the `trace_event_id` is unique to each event (row), the
`trace_id` is only unique to a *group of connected events* ("a trace").

## okdata-aws
The master of event data is defined in the
[okdata-aws](https://github.com/oslokommune/okdata-aws) library:

### okdata.aws.status
Exposes a
[decorator](https://github.com/oslokommune/okdata-aws/blob/master/okdata/aws/status/wrapper.py)
to use in Lambda functions. See
[s3-writer](https://github.com/oslokommune/okdata-pipeline/blob/master/okdata/pipeline/writers/s3/handlers.py)
for an example of using `@status_wrapper`. This will send a status to the status
API after execution of the handler is done. The minimum that should be done is
to set `domain` and `domain_id` on the status object using
`status_add(domain="dataset", ...)`.

Setting the `status_body` with `status_add(status_body={"files_incoming": [],
"files_outgoing": [], "other": "relevant_information"})`, the user can retrieve
information on what has happened in each step going through the system.
Generally it is best practice to log as much you can to the `status_body` field
in order for the end-user to be able to trace what has happened to the data.

If the Lambda handler fails (e.g. throws an unhandled exception), the wrapper
automatically updates the event status to `FAILED` and trace status to
`FINISHED`.

## Data uploader
The [data-uploader](https://github.com/oslokommune/okdata-data-uploader) creates
a trace ID whenever a file is uploaded via the API. The trace ID is returned to
the user when uploaded. This trace ID is the one the pipeline-router (see below)
will pick up and set as execution name.

To extract the trace ID after uploading a file to a dataset via the okdata CLI:
```sh
okdata datasets cp /tmp/hello.xlsx ds:my-dataset --format=json | jq -r ".trace_id"
```

## Pipeline router
The [pipeline-router](https://github.com/oslokommune/okdata-pipeline-router) is
integrated with the status API and will use the API to retrieve the trace ID for
the current execution.

The pipeline-router is executed based on an S3-event in AWS. The S3-path in the
event is sent to `http://{API}/status-from-path/{s3_path}` to retrieve the
corresponding trace ID. Once retrieved the trace ID is set as the execution name
on the state machine.

Each execution step in the state machine will now have access to the trace ID
via the `execution_name`. When using the `@status_wrapper` this value will be
extracted and populated for you.

A `state-machine-event` Lambda function is hooked up to CloudFormation logs (see
[dataplatform-config](https://github.com/oslokommune/dataplatform-config/tree/main/devops/modules/observability/cloudwatch-state-machine-events)
for wiring) that will pick up the end status for the state machine and post this
to the status API. There is no need to set the end status from within the Lambda
function, only the state of each execution. This means you can get the end
status of a file-upload without adding anything to the state machine functions.

## SDK & CLI
The status API is implemented in the SDK and exposed via the CLI:

### Get the total status of an ID
```sh
$ okdata status eide-origo-ng-85c9e5de-ac38-4b37-af8a-a86f08ce2bbb
Status for: eide-origo-ng-85c9e5de-ac38-4b37-af8a-a86f08ce2bbb
+------+----------------------------------------------------+--------------+--------------------+
| Done |                     Trace ID                       | Trace status | Trace event status |
+------+----------------------------------------------------+--------------+--------------------+
| True | eide-origo-ng-85c9e5de-ac38-4b37-af8a-a86f08ce2bbb | FINISHED     | OK                 |
+------+----------------------------------------------------+--------------+--------------------+
```
### Get the total status of an ID as pure JSON
```sh
$ okdata status eide-origo-ng-85c9e5de-ac38-4b37-af8a-a86f08ce2bbb --format=json
{
  "done": true,
  "trace_id": "eide-origo-ng-85c9e5de-ac38-4b37-af8a-a86f08ce2bbb",
  "trace_status": "FINISHED",
  "trace_event_status": "OK"
}
```
### Get just the done status
```sh
$ okdata status eide-origo-ng-85c9e5de-ac38-4b37-af8a-a86f08ce2bbb --format=json | jq -r ".done"
true
```
### Get the full history of an ID
```sh
$ okdata status eide-origo-ng-85c9e5de-ac38-4b37-af8a-a86f08ce2bbb --history
```
Will print a table with information on each step through the system. Depends on
`@status_wrapper` being used in each Lambda function.
