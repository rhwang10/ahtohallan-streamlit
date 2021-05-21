import boto3
import os

from boto3.dynamodb.conditions import Key, Attr

PK = "emoji_id|emoji_name"
SK = "author_id|timestamp"
METADATA = "METADATA"

class EmojiEvents:

    def __init__(self):
        aws_access_key = os.environ.get("AWS_ACCESS_KEY")
        aws_secret_key = os.environ.get("AWS_SECRET_KEY")
        table_name = os.environ.get("ELSA_EMOJI_DDB_TABLE")

        if not aws_access_key or not aws_secret_key or not table_name:
            raise Exception("Unable to initialize Dynamo client, missing AWS access key, AWS secret key, or table name. Check environmental variables")

        dynamo = boto3.resource(
            'dynamodb',
            'us-east-1',
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key
        )

        self.table = dynamo.Table(table_name)

    def get_all_emojis(self):
        response = self.table.scan(
            FilterExpression = Attr(SK).eq(METADATA)
        )["Items"]

        return response if response else []