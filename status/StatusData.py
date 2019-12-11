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
        log.info(f"Trying to write {id} to database with type {type(id)}")
        log.info(
            f"Trying to write dato to database with type {type(datetime.datetime.now())}"
        )
        log.info(
            f"Trying to write processStatus to database with type {type('STARTED')}"
        )
        db_response = self.table.put_item(
            Item={
                "uuid": id,
                "dato": datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
                "processStatus": "STARTED",
            }
        )

        return db_response

    def get_status(self, id):
        key = {"uuid": id}
        db_response = self.table.get_item(Key=key)
        return db_response
        
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
        return db_response
