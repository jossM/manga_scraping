from datetime import datetime
import warnings

from type.chapter import Chapter
from dynamo import base_type


class PageMark(base_type.BaseDynamoORM):
    @classmethod
    def dynamo_table_name(cls) -> str:
        return 'manga_page_marks'

    _DATE_FORMAT = '%Y-%m-%d %H:%M:%s'

    def __init__(self, serie_id: str, serie_name: str=None, latest_update: str=None, chapter_mark: str= None):
        self.serie_id = serie_id
        warning_message = f'Corrupted PageMark document for serie {self.serie_id}.'
        will_raise_warning = False

        self.serie_name = serie_name
        if self.serie_name is None:
            will_raise_warning = True
            warning_message += ' "serie_name" attribute is missing.'
        try:
            self.latest_update = datetime.strptime(latest_update, self._DATE_FORMAT)
        except TypeError:  # handles None values
            self.latest_update = None
        except ValueError:  # handles badly formatted dates
            self.latest_update = None
            will_raise_warning = True
            warning_message += f' "latest_date" attribute has a date {latest_update}' \
                               f' that does not correspond to schema {self._DATE_FORMAT}.'
        self.chapter_mark = Chapter(chapter_mark)
        if not self.chapter_mark.is_valid():
            will_raise_warning = True
            warning_message += f'  "latest_date" attribute has an unhandled format.'
        if will_raise_warning:
            warnings.warn(warning_message, base_type.CorruptedDynamoDbBase)
