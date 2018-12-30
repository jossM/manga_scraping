from abc import abstractmethod
import re
from typing import Union, Generic, TypeVar, Dict, Any

from logs import logger

_SerializableClass = TypeVar('_SerializableClass')
LETTER_GROUP = 'letter'
NUMBER_GROUP = 'number'


def make_regex(keyword: str):
    return re.compile(f'^{keyword} ?(?P<{NUMBER_GROUP}>[0-9]*)$')


class Serializable(Generic[_SerializableClass]):
    """ abstract class """
    @classmethod
    @abstractmethod
    def deserialize(cls, dict_data: Dict) -> _SerializableClass:
        ...

    @abstractmethod
    def serialize(self) -> Dict[str, Any]:
        ...


class UnknownChapterFormat(UserWarning):
    pass


class Chapter(Serializable):
    """ represents all the logic to work with a chapter """
    def __init__(self, chapter: str, volume: Union[None, int] = None):
        if isinstance(volume, str) and not volume.strip():
            self.volume = None
        self.volume = volume
        self.chapter = chapter.strip()

    def __ge__(self, other: 'Chapter'):
        if self.__gt__(other):
            return True
        return self.volume == other.volume and self.get_chapter_val() == self.get_chapter_val()
        # /!\ Careful you can have chap1 > chap2 -> False and chap1 >= chap2 -> True but chap1 == chap2 false
        # as == is not used here

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

    def __hash__(self) -> int:
        return hash((self.volume, self.chapter))

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        fromated_value = re.sub(r'e\+0+', 'e+', '{:.1e}'.format(self.get_chapter_val()))
        fromated_value = re.sub(r'e\+$', '', fromated_value)
        fromated_value = re.sub(r'\.0+', '', fromated_value)
        return f'volume: {self.volume}, \tchapter: "{self.chapter}" (value: {fromated_value})'

    regex_values_mapping = [
        (-2000000, make_regex('oneshot')),
        (-1500000, make_regex('drama cd')),
        (-1000000, make_regex('extra')),
        (-1000000, make_regex('omakes')),
        (-500000, make_regex('special')),
        (-100000, make_regex('prologue')),
        (9000000, make_regex('epilogue')),
    ]

    sub_version_letter = re.compile(f'^(?P<{NUMBER_GROUP}>[0-9]+)(?P<{LETTER_GROUP}>[a-z])$')
    version_regex = re.compile(f'^(?P<{NUMBER_GROUP}>[0-9]+)v[0-9]+$')

    def get_chapter_val(self) -> float:
        """ implements parsing logic for manga chapters (prologue, oneshot, 24.1, 24 etc... """
        try:
            return float(self.chapter)
        except (ValueError, TypeError):
            pass
        if self.chapter is None:
            return float(-9000000)
        attached_string_chapter = re.sub(r'[\W]--[ ]]+', '', self.chapter).lower().strip()
        for value, regexp in self.regex_values_mapping:
            matched = regexp.match(attached_string_chapter)
            if not matched:
                continue
            number_string = matched.group(NUMBER_GROUP)
            if not number_string:
                return float(value)
            sub_info = int(number_string)
            return float(value + sub_info)
        sub_version_matched = self.sub_version_letter.match(attached_string_chapter)
        if sub_version_matched:
            sub_version = ord(sub_version_matched.group(LETTER_GROUP)) - ord('a') + 1
            chapter_num = int(sub_version_matched.group(NUMBER_GROUP))
            return chapter_num + sub_version/10
        matched_version = self.version_regex.match(attached_string_chapter)
        if matched_version:
            return float(matched_version.group(NUMBER_GROUP))
        logger.warning(f'Unsupported chapter type for comparison "{self.chapter}" '
                       f'(volume {self.volume} - "{attached_string_chapter}")')
        return -1

    def is_valid(self) -> bool:
        """ whether the current chapter can be given an acceptable value or has a default one"""
        if self.volume is not None and not isinstance(self.volume, int):
            return False
        try:
            self.get_chapter_val()
        except UnknownChapterFormat:
            return False
        return True

    def serialize(self) -> Dict[str, Union[int, str]]:
        """ transforms the objet into a dict to be stored in dynamodb """
        if self.volume is None:
            return dict(chapter=self.chapter)
        return dict(volume=self.volume, chapter=self.chapter)

    @classmethod
    def deserialize(cls, dict_data: Dict[str, Union[int, str]]) -> 'Chapter':
        """ inverse of serialize method transforms a dict into a chapter """
        if 'volume' in dict_data:
            dict_data['volume'] = int(dict_data['volume'])
        return cls(**dict_data)
