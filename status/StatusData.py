import boto3
import logging
import json
import datetime

log = logging.getLogger()


class StatusData:
    def __init__(self):
        dynamodb = boto3.resource("dynamodb", "eu-west-1")
        self.table = dynamodb.Table("status_data")

    def create_item(self, id, status):
        db_response = self.table.put_item(
            Item={
                'uuid': id,
                'dato': datetime.datetime.now().timestamp(),
                'status': status
            }
        )
        print("PutItem succeeded:")
        print(json.dumps(db_response))

    def get_status(self, id):
        key = {"uuid": id}
        db_response = self.table.get_item(Key=key)

        if "Item" in db_response:
            status = db_response["Item"]["status"]
            log.info(f"Found status {status}")
            return {"statusCode": 200, "process_status": json.dumps(db_response["Item"]["status"])}

        log.info(f"Status not found for {db_response['Item']}")
        return {"statusCode": 404, "body": json.dumps("Could not find item.")}

    def update_status(self, id, status):
        key = {"uuid": id}
        db_response = self.table.update_item(
            Key=key,
            UpdateExpression="set date = :d, status = :s",
            ExpressionAttributeValues={
                ":d": datetime.datetime.now().timestamp(),
                ":s": status,
            },
            ReturnValues="UPDATED_NEW",
        )

        if "Item" in db_response:
            item = db_response["Item"]
            log.info(f"Updatet status {item}")
            return status

        log.info(f"Item {id} not found")
        return None
