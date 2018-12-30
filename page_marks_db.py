from datetime import datetime
import inspect
import pytz
from typing import List, Dict, Union, Iterable

import boto3
from botocore.exceptions import ClientError

from config import AWS_REGION
from global_types import Chapter, Serializable
from logs import logger


dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)

DYNAMO_TABLE = dynamodb.Table('manga_page_marks')


class CorruptedDynamoDbBase(UserWarning):
    pass


class PageMark(Serializable):
    """ ORM for table manga_page_marks on dynamodb"""

    def __init__(self,
                 serie_id: str,
                 serie_name: Union[str, None]=None,
                 img_link: Union[str, None]=None,
                 latest_update: Union[datetime, None]=None,
                 chapter_marks: Union[List[Chapter], None]= None):
        self._serie_id = serie_id
        self.serie_name = serie_name
        self.img_link = img_link
        self.latest_update = latest_update
        if chapter_marks is None:
            self.chapter_marks: List[Chapter] = []
        else:
            self.chapter_marks: List[Chapter] = sorted(chapter_marks, reverse=True)

    @property
    def serie_id(self) -> str:
        """ serie id is immutable """
        return self._serie_id

    def __hash__(self) -> int:
        return hash(self._serie_id)

    def __contains__(self, item: Chapter) -> bool:
        return item in self.chapter_marks

    def __iter__(self):
        for chapter in self.chapter_marks:
            yield chapter

    def __repr__(self) -> str:
        type_string = str(type(self))
        header_sep = '\n\t'
        chapter_sep = header_sep + '\t'
        repr_string = f'{type_string}<' \
                      f'{header_sep}serie: {self.serie_id}' \
                      f'{header_sep}name: {self.serie_name}' \
                      f'{header_sep}image link: {self.img_link}{chapter_sep}'
        repr_string += chapter_sep.join(f'chapter {chapter}' for chapter in self) + '>'
        return repr_string

    def extend(self, chapters: Iterable[Chapter]) -> 'PageMark':
        """ offers easy implementation to add chapters to chapter marks """
        new_chapter_marks = [chapter for chapter in chapters if chapter not in self]
        self.chapter_marks = sorted(new_chapter_marks + self.chapter_marks,  reverse=True)
        return self

    def serialize(self) -> Dict:
        serialized_mark = dict(serie_id=self.serie_id)
        if self.serie_name is not None:
            serialized_mark['serie_name'] = self.serie_name
        if self.latest_update is not None:
            serialized_mark['latest_update'] = self.latest_update.astimezone(pytz.utc).isoformat()
        if self.chapter_marks:
            serialized_mark['chapter_marks'] = [chapter.serialize() for chapter in self.chapter_marks]
        if self.img_link:
            serialized_mark['img_link'] = self.img_link
        return serialized_mark

    @classmethod
    def deserialize(cls, dict_data: Dict) -> 'PageMark':
        """ transform a dict into an objet. may trigger warnings if object does not have the correct format """
        deserialized_page_mark = cls(serie_id=dict_data['serie_id'])
        warning_message = f'Corrupted PageMark document for serie id {deserialized_page_mark.serie_id}.'
        initial_warning_message_len = len(warning_message)

        serie_name = dict_data.get('serie_name', None)
        if 'serie_name' not in dict_data:
            warning_message += '\n"serie_name" attribute is missing.'
        else:
            deserialized_page_mark.serie_name = dict_data['serie_name']
            warning_message += f' name "{serie_name}"'
            initial_warning_message_len = len(warning_message)
        if 'img_link' not in dict_data:
            warning_message += '\n"img_link" attribute is missing.'
        else:
            deserialized_page_mark.img_link = dict_data['img_link']

        if 'latest_update' in dict_data:
            deserialized_page_mark.latest_update = dict_data['latest_update']

        raw_chapter_marks = dict_data.get('chapter_marks', [])
        chapter_marks = list()
        for index_position, mark in enumerate(raw_chapter_marks):
            try:
                chapter = Chapter.deserialize(mark)
                if not chapter.is_valid():
                    warning_message += f' chapter_mark" attribute is invalid at position. {index_position},' \
                                       f' with key values "{str(mark)}"'
                chapter_marks.append(chapter)
            except TypeError:
                warning_message += f' chapter_mark" attribute is invalid at position. {index_position},' \
                                   f' with key values "{str(mark)}"'
        deserialized_page_mark.chapter_marks = sorted(chapter_marks, reverse=True)

        if len(warning_message) > initial_warning_message_len:
            logger.warning(warning_message)
        return deserialized_page_mark


def get_all() -> List[PageMark]:
    """ Get all page coming from db. """
    attributes = list(inspect.signature(PageMark.__init__).parameters.keys())
    attributes.remove('self')
    response = DYNAMO_TABLE.scan(ProjectionExpression=', '.join(attributes))
    return [PageMark.deserialize(page_mark_elem) for page_mark_elem in response['Items']]


def get(serie_id: str) -> Union[None, PageMark]:
    """ Retrieves a page mark object from db or returns None if no matching key is found. """
    try:
        response = DYNAMO_TABLE.get_item(Key=dict(serie_id=serie_id))
    except ClientError:
        logger.error('failed to get ', exc_info=True)
        return None
    return PageMark.deserialize(response['Item'])


def batch_put(page_marks: Iterable[PageMark]) -> None:
    """ writes on dynamodb table"""
    with DYNAMO_TABLE.batch_writer() as batch:
        for page_mark in page_marks:
            batch.put_item(Item=page_mark.serialize())


def put(page_mark: PageMark) -> None:
    """ writes on dynamodb table"""
    DYNAMO_TABLE.put_item(Item=page_mark.serialize())
