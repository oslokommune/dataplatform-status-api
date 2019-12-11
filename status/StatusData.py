import boto3
import logging
import json
import datetime

log = logging.getLogger()


class StatusData:
    def __init__(self):
        dynamodb = boto3.resource("dynamodb", "eu-west-1")
        self.table = dynamodb.Table("status_data")

    def create_item(self, id):
        db_response = self.table.put_item(
            Item={
                'uuid': id,
                'dato': datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
                'processStatus': 'STARTED'
            }
        )

        return db_response

    def get_status(self, id):
        key = {"uuid": id}
        db_response = self.table.get_item(Key=key)

        if "Item" in db_response:
            status = db_response["Item"]["processStatus"]
            log.info(f"Found processStatus {status}")
            return {
                "statusCode": 200,
                "process_status": json.dumps(db_response["Item"]["processStatus"]),
            }

        log.info(f"Status not found for {db_response['Item']}")
        return {"statusCode": 404, "body": json.dumps("Could not find item.")}

    # TODO##":d": datetime.datetime.now().timestamp(), må konverters fra float til desimal
    # dato = :d,
    def update_status(self, id, status):
        key = {"uuid": id}
        db_response = self.table.update_item(
            Key=key,
            UpdateExpression="SET dato = :d, processStatus = :s",
            ExpressionAttributeValues={
                ":d": datetime.datetime.now().strftime("%d/%m/%Y, %H:%M:%S"),
                ":s": status,
            },
        )
        if "Item" in db_response:
            status = db_response["Item"]["processStatus"]
            log.info(f"Found status {status}")
            return {
                "statusCode": 200,
                "process_status": json.dumps(db_response["Item"]["processStatus"]),
            }
        else:
            log.info(f"Status not found for {id}")
            return {"statusCode": 404, "body": json.dumps("Could not find item.")}
