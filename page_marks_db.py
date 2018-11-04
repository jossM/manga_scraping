from datetime import datetime
import inspect
import os
from typing import List

import boto3


dynamodb = boto3.resource('dynamodb', region_name=os.environ.get('AWS_REGION'))  #todo pass in config file


class PageMark(object):
    _TABLE = dynamodb.Table('manga_page_marks')
    _DATE_FORMAT = '%Y-%m-%d %H:%M:%s'

    def __init__(self, serie_id: str, serie_name: str=None, latest_update: str=None, chapter_mark: str= None):
        self.serie_id = serie_id
        self.serie_name = serie_name # todo warning if None?
        try:
            self.latest_update = datetime.strptime(latest_update, self._DATE_FORMAT)
        except (ValueError, TypeError):
            self.latest_update = None
        self.chapter_mark = chapter_mark

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
