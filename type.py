import re
from typing import Union


class UnknownChapterFormat(ValueError):
    pass


class Chapter(object):
    def __init__(self, chapter: Union[str, None]):
        self._chapter = chapter

    def __ge__(self, other: 'Chapter'):
        return self._get_val() >= other._get_val()

    def __gt__(self, other: 'Chapter'):
        return self._get_val() > other._get_val()

    def __eq__(self, other: 'Chapter'):
        return self._get_val() == other._get_val()

    def __ne__(self, other: 'Chapter'):
        return self._get_val() != other._get_val()

    def __str__(self):  # used to serialize
        return self.chapter

    def _get_val(self) -> float:
        """ implements parsing logic for manga chapters (prologue, oneshot, 24.1, 24 etc... """
        if self.chapter is None:
            return -1000
        attached_string_chapter = re.sub(r'[\W]--[ ]]+', '', self.chapter).lower()
        if attached_string_chapter == 'oneshot':
            return -2
        if attached_string_chapter == 'prologue':
            return -1
        try:
            return float(self.chapter)
        except ValueError:
            raise UnknownChapterFormat(f'Unsupported chapter type for comparison {self.chapter}')

    def is_valid(self):
        try:
            self._get_val()
        except UnknownChapterFormat:
            return False
        return True

    @property
    def chapter(self):
        return self._chapter
