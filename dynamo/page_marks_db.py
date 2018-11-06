from datetime import datetime
from typing import List, Dict, Any
import warnings

from chapter_type import Chapter
from dynamo import base_type


class PageMark(base_type.BaseDynamoORM):
    @classmethod
    def dynamo_table_name(cls) -> str:
        return 'manga_page_marks'

    _DATE_FORMAT = '%Y-%m-%d %H:%M:%s'

    def __init__(self, serie_id: str, serie_name: str=None, latest_update: str=None, chapter_marks: List[str]= None):
        self.serie_id = serie_id
        warning_message = f'Corrupted PageMark document for serie {self.serie_id}.'
        initial_warning_message_len = len(warning_message)

        self.serie_name = serie_name
        if self.serie_name is None:
            warning_message += ' "serie_name" attribute is missing.'
        try:
            self.latest_update = datetime.strptime(latest_update, self._DATE_FORMAT)
        except TypeError:  # handles None values
            self.latest_update = None
        except ValueError:  # handles badly formatted dates
            self.latest_update = None
            warning_message += f' "latest_date" attribute has a date {latest_update}' \
                               f' that does not correspond to schema {self._DATE_FORMAT}.'
        self.chapter_marks = []
        if chapter_marks is None:
            warning_message += f' "chapter_marks" attribute is missing.'
        else:
            for index_position, mark in enumerate(chapter_marks):
                chapter = Chapter(mark)
                if chapter.is_valid():
                    self.chapter_marks.append(chapter)
                else:
                    warning_message += f'\n"chapter_mark" attribute is invalid at position. {index_position},' \
                                       f' with value "{str(chapter)}"'
            self.chapter_marks = sorted(self.chapter_marks, reverse=True)
        if len(warning_message) > initial_warning_message_len:
            warnings.warn(warning_message, base_type.CorruptedDynamoDbBase)

    def serialize(self) -> Dict[str, Any]:
        serialized = super().serialize()
        serialized['chapter_marks'] = [str(chapter) for chapter in self.chapter_marks]
        return serialized
