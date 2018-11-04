from datetime import datetime
import inspect
import os
from typing import List
import warnings

import boto3

from type import Chapter

dynamodb = boto3.resource('dynamodb', region_name=os.environ.get('AWS_REGION'))


class CorruptedDynamoDbBase(UserWarning):
    pass


class PageMark(object):
    _TABLE = dynamodb.Table(os.environ.get('PAGE_MARKS_TABLE'))
    _DATE_FORMAT = '%Y-%m-%d %H:%M:%s'

    def __init__(self, serie_id: str, serie_name: str=None, latest_update: str=None, chapter_mark: str= None):
        warning = f'Corrupted PageMark document for serie {self.serie_id}.'
        will_raise_warning = False

        self.serie_id = serie_id
        self.serie_name = serie_name
        if self.serie_name is None:
            will_raise_warning = True
            warning += ' "serie_name" attribute is missing.'
        try:
            self.latest_update = datetime.strptime(latest_update, self._DATE_FORMAT)
        except TypeError:  # handles None values
            self.latest_update = None
        except ValueError:  # handles badly formatted dates
            will_raise_warning = True
            warning += f' "latest_date" attribute has a date {latest_update}' \
                       f' that does not correspond to schema {self._DATE_FORMAT}.'
        self.chapter_mark = Chapter(chapter_mark)
        if not self.chapter_mark.is_valid():
            will_raise_warning = True
            warning += f'  "latest_date" attribute has an unhandled format.'
        if will_raise_warning:
            warnings.warn(warning, CorruptedDynamoDbBase)

    def __repr__(self):
        return '{' + ', '.join([f'{attribute}:{getattr(self, attribute)}'
                                for attribute in inspect.signature(self.__init__).parameters]) + '}'

    @classmethod
    def get_all(cls) -> List['PageMark']:
        keys = list(inspect.signature(cls.__init__).parameters.keys())
        keys.remove('self')
        response = cls._TABLE.scan(ProjectionExpression=', '.join(keys))
        return [cls(**page_mark_elem) for page_mark_elem in response['Items']]

    def put(self) -> None:
        ...  # todo
