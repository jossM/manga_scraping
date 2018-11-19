from datetime import datetime
import inspect
import os
import pytz
from typing import List, Dict, Any, Union
import warnings

import boto3

from global_types import Chapter, Serializable


dynamodb = boto3.resource('dynamodb', region_name=os.environ.get('AWS_REGION'))


class CorruptedDynamoDbBase(UserWarning):
    pass


class PageMark(Serializable):
    """ ORM for table manga_page_marks on dynamodb"""
    DYNAMO_TABLE = dynamodb.Table('manga_page_marks')

    def __init__(self,
                 serie_id: str,
                 serie_name: Union[str, None]=None,
                 latest_update: Union[datetime, None]=None,
                 chapter_marks: Union[List[Chapter], None]= None):
        self.serie_id = serie_id
        self.serie_name = serie_name
        self.latest_update = latest_update
        if chapter_marks is None:
            self.chapter_marks = []
        else:
            self.chapter_marks = chapter_marks

    def put(self) -> None:
        type(self).DYNAMO_TABLE.put_item(Item=self.serialize())

    @classmethod
    def get_all(cls) -> List['PageMark']:
        response = cls.DYNAMO_TABLE.scan(ProjectionExpression=', '.join(cls.get_dynamo_db_attributes()))
        return [cls.deserialize(page_mark_elem) for page_mark_elem in response['Items']]


    @classmethod
    def get_dynamo_db_attributes(cls):
        attributes = list(inspect.signature(cls.__init__).parameters.keys())
        attributes.remove('self')
        return attributes

    def serialize(self) -> Dict[str, Any]:
        serialized_mark = dict(serie_id=self.serie_id)
        if self.serie_name is not None:
            serialized_mark['serie_name'] = self.serie_name
        if self.latest_update is not None:
            serialized_mark['latest_update'] = self.latest_update.astimezone(pytz.utc).isoformat()
        if self.chapter_marks:
            serialized_mark['chapter_marks'] = []
        return serialized_mark

    @classmethod
    def deserialize(cls, dict_data: Dict) -> 'PageMark':
        deserialized_page_mark = cls(dict_data['serie_id'])
        warning_message = f'Corrupted PageMark document for serie id {deserialized_page_mark.serie_id}.'
        initial_warning_message_len = len(warning_message)

        serie_name = dict_data.get('serie_name', None)
        if 'serie_name' not in dict_data:
            warning_message += '\n"serie_name" attribute is missing.'
        else:
            deserialized_page_mark.serie_name = dict_data['serie_name']
            warning_message += f' name "{serie_name}"'
            initial_warning_message_len = len(warning_message)
        if 'latest_update' in dict_data:
            try:
                deserialized_page_mark.latest_update = datetime.fromisoformat(dict_data['latest_update'])
            except ValueError:  # handles badly formatted dates
                warning_message += \
                    f'\nfailed to parse "latest_date" attribute as an iso 8601 date. Attribute value was ' \
                    f'{dict_data["latest_update"]}'

        raw_chapter_marks = dict_data.get('chapter_marks', [])
        chapter_marks = list()
        for index_position, mark in enumerate(raw_chapter_marks):
            try:
                chapter = Chapter(**mark)
                if not chapter.is_valid():
                    warning_message += f' chapter_mark" attribute is invalid at position. {index_position},' \
                                       f' with key values "{str(mark)}"'
                chapter_marks.append(chapter)
            except TypeError:
                warning_message += f' chapter_mark" attribute is invalid at position. {index_position},' \
                                   f' with key values "{str(mark)}"'
        deserialized_page_mark.chapter_marks = sorted(chapter_marks, reverse=True)
        if len(warning_message) > initial_warning_message_len:
            warnings.warn(warning_message, CorruptedDynamoDbBase)
        return deserialized_page_mark
