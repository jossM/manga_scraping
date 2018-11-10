import re
from typing import Union, List
import warnings


class UnknownChapterFormat(UserWarning):
    pass


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


def get_min_diff_between_chapters(chapters: List[Chapter], already_sorted= False) -> float:
    default_return = 1.
    if not already_sorted:
        chapters = sorted(chapters)
    if not chapters:
        return default_return
    diffs = [abs(chapters[i] - chapters[i + 1]) for i in range(len(chapters)-1)]
    if max(diffs) == 0:
        return default_return
    return next(dif for dif in diffs if dif)
