from decimal import Decimal
import re
from typing import Union
import warnings


class UnknownChapterFormat(UserWarning):
    pass


class Chapter(object):
    def __init__(self, chapter: str, volume: Union[None, int] = None):
        if isinstance(volume, str) and not volume.strip():
            self.volume = None
        self.volume = volume
        self.chapter = chapter.strip()

    def __ge__(self, other: 'Chapter'):
        if self.__gt__(other):
            return True
        return self.volume == other.volume and self.get_chapter_val() == self.get_chapter_val()

    def __gt__(self, other: 'Chapter'):
        if self.volume is None and other.volume is not None:
            return False
        if other.volume is None and self.volume is not None:
            return True
        if self.volume is not None and other.volume is not None:
            if self.volume > other.volume:
                return True
        return self.get_chapter_val() > other.get_chapter_val()

    def __lt__(self, other: 'Chapter'):
        return not self.__ge__(other)

    def __le__(self, other: 'Chapter'):
        return not self.__gt__(other)

    def __eq__(self, other: 'Chapter'):
        if self.volume != other.volume:
            return False
        return self.chapter == other.chapter

    def __ne__(self, other: 'Chapter'):
        return not self.__eq__(other)

    def __str__(self) -> str:  # used to serialize
        fromated_value = re.sub(r'e\+0+', 'e+', '{:.1e}'.format(self.get_chapter_val()))
        fromated_value = re.sub(r'e\+$', '', fromated_value)
        fromated_value = re.sub(r'\.0+', '', fromated_value)
        return str(f'volume: {self.volume}, \tchapter: "{self.chapter}" (value: {fromated_value})')

    def __hash__(self):
        return hash((self.volume, self.chapter))

    def get_chapter_val(self) -> float:
        """ implements parsing logic for manga chapters (prologue, oneshot, 24.1, 24 etc... """
        if self.chapter is None:
            return float(-9000000)
        attached_string_chapter = re.sub(r'[\W]--[ ]]+', '', self.chapter).lower()
        if attached_string_chapter == 'oneshot':
            return float(-2000000)
        if attached_string_chapter == 'prologue':
            return float(-1000000)
        if attached_string_chapter == 'epilogue':
            return float(9000000)
        try:
            return float(self.chapter)
        except (ValueError, TypeError):
            warnings.warn(f'Unsupported chapter type for comparison {self.chapter}', UnknownChapterFormat)
        return 0

    def is_valid(self):
        if self.volume is not None and not isinstance(self.volume, int):
            return False
        try:
            self.get_chapter_val()
        except UnknownChapterFormat:
            return False
        return True
