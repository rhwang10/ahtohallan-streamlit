import boto3
import os
import streamlit as st

from boto3.dynamodb.conditions import Key, Attr

PK = "emoji_id|emoji_name"
SK = "author_id|timestamp"
METADATA = "METADATA"

class EmojiEvents:

    def __init__(self):
        aws_access_key = st.secrets["dynamo_credentials"]["access_key"]
        aws_secret_key = st.secrets["dynamo_credentials"]["secret_key"]
        table_name = st.secrets["dynamo_credentials"]["emoji_events_table_name"]

        if not aws_access_key or not aws_secret_key or not table_name:
            raise Exception("Unable to initialize Dynamo client, missing AWS access key, AWS secret key, or table name. Check environmental variables or TOML file")

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
        )

        return response["Items"] if response else []


    def get_all_emojis_by_author(self, pk, author_id):
        response = self.table.query(
            KeyConditionExpression=Key(PK).eq(pk) & Key(SK).begins_with(author_id)
        )
        return response["Items"] if response else []
