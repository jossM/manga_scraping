import re
from typing import Union, TypeVar
import warnings


class UnknownChapterFormat(UserWarning):
    pass

ChapterType = TypeVar('ChapterType')

class Chapter(object):
    def __init__(self, chapter: Union[str, None]):
        self._chapter = chapter

    def __ge__(self, other: 'Chapter'):
        return self.get_val() >= other.get_val()

    def __gt__(self, other: 'Chapter'):
        return self.get_val() > other.get_val()

    def __eq__(self, other: 'Chapter'):
        return self.get_val() == other.get_val()

    def __ne__(self, other: 'Chapter'):
        return self.get_val() != other.get_val()

    def __str__(self) -> str:  # used to serialize
        return str(self._chapter)

    def __cmp__(self, other: Union['Chapter', float, int]):
        if isinstance(other, Chapter):
            return self.get_val().__cmp__(other.get_val())
        return self.get_val().__cmp__(float(other))

    def __hash__(self):
        return hash(self._chapter)

    def __sub__(self, other: 'Chapter'):
        return self.get_val() - other.get_val()

    def get_val(self) -> float:
        """ implements parsing logic for manga chapters (prologue, oneshot, 24.1, 24 etc... """
        if self._chapter is None:
            return -float('inf')
        attached_string_chapter = re.sub(r'[\W]--[ ]]+', '', self._chapter).lower()
        if attached_string_chapter == 'oneshot':
            return float(-2)
        if attached_string_chapter == 'prologue':
            return float(-1)
        if attached_string_chapter == 'epilogue':
            return float('inf')
        try:
            return float(self._chapter)
        except ValueError:
            warnings.warn(f'Unsupported chapter type for comparison {self._chapter}', UnknownChapterFormat)
        return 0

    def is_valid(self):
        try:
            self.get_val()
        except UnknownChapterFormat:
            return False
        return True
