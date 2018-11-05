from abc import abstractmethod
import inspect
import os
from typing import List, Generic, TypeVar

import boto3


dynamodb = boto3.resource('dynamodb', region_name=os.environ.get('AWS_REGION'))


class CorruptedDynamoDbBase(UserWarning):
    pass


_DynamoType = TypeVar('_DynamoType')


class BaseDynamoORM(Generic[_DynamoType]):
    @classmethod
    @abstractmethod
    def dynamo_table_name(cls) -> str:
        ...

    @classmethod
    def dynamo_table(cls) -> dynamodb.Table:
        return dynamodb.Table(cls.dynamo_table_name())

    @classmethod
    def dynamo_db_attributes(cls) -> List[str]:
        attributes = list(inspect.signature(cls.__init__).parameters.keys())
        attributes.remove('self')
        return attributes

    @classmethod
    def get_all(cls) -> List[_DynamoType]:
        response = cls.dynamo_table().scan(ProjectionExpression=', '.join(cls.dynamo_db_attributes()))
        return [cls(**page_mark_elem) for page_mark_elem in response['Items']]

    def put(self) -> None:
        dynamo_table = dynamodb.Table(super(self).dynamo_db_attributes())
        dynamo_table.put_item(
            Item={attribute: getattr(self, attribute) for attribute in type(self).dynamo_db_attributes()})

    def __repr__(self) -> str:
        return '{' + ', '.join([f'{attribute}:{getattr(self, attribute)}'
                                for attribute in type(self).dynamo_db_attributes()]) + '}'
