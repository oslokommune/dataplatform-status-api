# status-api
API for tracking status through a asynchronous system

## Install/Setup
1. Install [Serverless Framework](https://serverless.com/framework/docs/getting-started/)
2. Setup venv
```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
3. Install Serverless plugins: `make init`
4. Install Python toolchain: `python3 -m pip install (--user) tox black pip-tools`
   - If running with `--user` flag, add `$HOME/.local/bin` to `$PATH`

# Status architecture
The status API defines a set of API endpoints to track events through a system from start to end. Initially created to track the exeuction state of a asynchronous state machine in AWS, it can be used for any task that needs to track the status from start to end: both synchronous and asynchronous executions.

Example: as a user I want to upload a file to a dataset I own. To ensure that the data has been processed, I need to know if the pipeline have executed successfully. Since the pipeline is asynchronous I don't get immediate feedback after uploading the file, I want to be able to query the system for the data-processing status.

The pseudo-code for the use-case is:

```
user -> upload file
  statusID = return value from upload process
user -> query status API for statusID
  repeat query until state is FINISHED
user -> check if status is FAILED or OK
  if status is FAILED -> get a list of what has been done within the pipeline and the reason for failing
  if status is OK -> continue with processing other data that relies on data processed in the above steps
```

Each Lambda function (see below) or step in the execution stage is responsible for setting the correct status for each step.

## Data lineage
The status API provides the status of a exeuction throughout a system, but it also have the added benefit that data lineage can be traced through the system at the same time. When using the `status_*` functions from common-python (or setting them manually on the status object), you can trace which application, application id and most important: which files was processed in each step, and what was the result of the data going out of each step in the function.

Setting the `body` with `status_add(body={"files_incoming": [], "files_outgoing": [], "other": "relevant_information"})` the user can retrieve information on what has happened in each step going through the system.

## Database structure
Database is setup in [dataplatform-config](https://github.oslo.kommune.no/origo-dataplatform/dataplatform-config/tree/master/devops/modules/services/status-api)

The main fields in the database:

| Field        | Type           | Description | Example |
|: ----------- |: -------------- |: ----------- |: -----------|
| id | string | The status ID used to trace connected events throughout the system (N-entries). Primary partition key | my-dataset-uu-ii-dd |
| event_id | uuid | Unique ID per event (many `event_id` per `id`) | uu-ii-dd |
| application | string | The application | dataset |
| application_id | string | A application specific ID to be able to look up the owner or source | dataset.name |
| date_started | time | Start of execution. Primary sort key | 2020-03-02T12:34:23.042400 |
| date_end | time | End of execution | 2020-03-02T12:34:24.042400 |
| handler | string | Who initiates the event | data-uploader, s3-writer |
| run_status | string | Overall status for the status ID | CONTINUE, FINISHED |
| status | string | Status for the `event_id` | OK, FAILED |
| user | string | The user that is used in `handler` to execute the event | service-user-s3-writer |
| s3path | string | Path of the uploaded file  | incoming/yellow/my-dataset/version/edition/file.xls |
| body | object | namespace where the event can add data relevant for the execution | {"files_incoming": [], "files_outgoing": []}|

`id` is not unique: the status of a event throughout a system will have many rows with identical `id` field, a `event_id` is unique


## Common Python
The master of status keys and values are defined in the [common-python](https://github.oslo.kommune.no/origo-dataplatform/common-python/blob/master/dataplatform/status/status.py) library:

### dataplatform/awslambda
Exposes a [decorator](https://github.oslo.kommune.no/origo-dataplatform/common-python/blob/master/dataplatform/awslambda/status.py) to use in lambda functions. See [s3-writer](https://github.oslo.kommune.no/origo-dataplatform/s3-writer/blob/master/writer/s3_writer.py) for a example of using `@status_wrapper`. This will send a status to the status API after execution of the handler is done. The minimum that should be done is to set `run_status` and `status` keys on the status object, if not the API will end up with `na` values

The library expose some `status_*` functions that can be used as shorthand functions in your lambda function to set the correct state of the execution, example: `status_end_continue(body={"files_incoming": []})`


### dataplatform/status
Holds the payload and constants that are the master values for the status API. Can be used self-contained to send status from a non-lambda function.

## Data uploader
The [data-uploader](https://github.oslo.kommune.no/origo-dataplatform/data-uploader/tree/master/uploader) creates a status ID whenever a file is uploaded via the API. The status ID is returned to the user when uploaded. This status ID is the one the pipeline-router (see below) will pick up and set as execution name.

To extract the status ID after uploading a file to a dataset via the origo CLI:
```
origo datasets cp /tmp/hello.xlsx ds:my-dataset --format=json | jq -r ".status"
```

## Pipeline router
The [pipeline-router](https://github.oslo.kommune.no/origo-dataplatform/pipeline-router) is integrated with the status API and will use the API to retrieve the status ID for the current execution.

The pipeline-router is executed based on a S3-event in AWS. The s3-path in the event is sent to `http://{API}/status-from-path/{s3path}` to retrive the corresponding status ID, once retrieved the status ID is set as the execution name on the state machine

Each execution step in the state machine will now have access to the status ID via the `execution_name` (see common-python/dataplatform/awslambda/status.py). When using the `@status_wrapper` this value will be extracted and populated for you.

A [state-machine-event](https://github.oslo.kommune.no/origo-dataplatform/state-machine-event) lambda function is hooked up to cloudformation logs (see [dataplatform-config](https://github.oslo.kommune.no/origo-dataplatform/dataplatform-config/tree/master/devops/modules/observability/cloudwatch-state-machine-events) for wiring) that will pick up the end status for the state machine and post this to the status API. There is no need to set the end status from within the lambda function, only the state of each execution. This means you can get the end status of a file-upload without adding anything to the state machine functions.

## Lambda
Use the `status_*` functions exposed via common-python to set the data for each Lambda exeuction.

Log as much you can to the `body` key in order for the end-user to be able to trace what has happened to the data

## SDK & CLI
The status API is implemented in the SDK and exposed via the CLI


### Get the total status of a ID
```
$ origo status eide-origo-ng-85c9e5de-ac38-4b37-af8a-a86f08ce2bbb
Status for: eide-origo-ng-85c9e5de-ac38-4b37-af8a-a86f08ce2bbb
+------+----------------------------------------------------+------------+--------+
| Done |                     Status ID                      | Run status | Status |
+------+----------------------------------------------------+------------+--------+
| True |eide-origo-ng-85c9e5de-ac38-4b37-af8a-a86f08ce2bbb |  FINISHED  |   OK   |
+------+----------------------------------------------------+------------+--------+
```
### Get the total status of a ID as pure json
```
$ origo status eide-origo-ng-85c9e5de-ac38-4b37-af8a-a86f08ce2bbb --format=json
{"done": true, "id": "eide-origo-ng-85c9e5de-ac38-4b37-af8a-a86f08ce2bbb", "run_status": "FINISHED", "status": "OK"}
```
### Get just the done status
```
$ origo status eide-origo-ng-85c9e5de-ac38-4b37-af8a-a86f08ce2bbb --format=json | jq -r ".done"
true
```
### Get the full history of a ID
```
$ origo status eide-origo-ng-85c9e5de-ac38-4b37-af8a-a86f08ce2bbb --history
```
Will print a table with information on each step through the system. Depends on `@status_wrapper` being used in each lambda function
