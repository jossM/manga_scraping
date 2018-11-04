from collections import namedtuple
from typing import Iterable, List, Union
from queue import Queue

from bs4 import BeautifulSoup
import requests

ChapterRelease = namedtuple('ChapterData', ['chapter', 'group'])


class ScrappedReleases(object):
    """ represents data returned from scrapping """
    def __init__(self, serie_id: str, chapters_releases: Iterable[ChapterRelease], warning_message=None):
        self.serie_id = serie_id
        self.warning_message = warning_message
        self.releases = list(chapters_releases) # todo sort them by decreasing order

    @property
    def warning(self) -> bool:
        return bool(self.warning_message)

    @property
    def latest_chapter_release(self) -> Union[None, ChapterRelease]:
        if not self.releases:
            return None
        return self.releases[-1]


def _extract_soup_data(soup: BeautifulSoup, tag: str) -> List[str]:
    """ extract all the data once on the correct div """
    result = list()
    for tag_soup in soup.find_all(tag):
        try:
            parsed_tag = next(tag_soup.children)
        except StopIteration:
            continue
        if not isinstance(parsed_tag, str):
            continue
        result.append(parsed_tag)
    return result


def scrap_bakaupdate(result_queue: Queue, serie_id: str) -> None:
    """
    Scraps data from bakaupdate for releases.
    Function to be executed in a thread to avoid waiting.
    """
    bakaupdate_page = requests.get(f'https://www.mangaupdates.com/series.html?id={serie_id}')
    bakaupdate_soup = BeautifulSoup(bakaupdate_page.content)
    latest_release_title_soup = bakaupdate_soup.find(string='Latest Release(s)').parent.parent
    latest_release_div_soup = latest_release_title_soup.find_next_sibling()
    chapters = _extract_soup_data(latest_release_div_soup, 'i')
    scanlation_groups = _extract_soup_data(latest_release_div_soup, 'a')
    warning_message = None
    if len(chapters) > len(scanlation_groups):
        warning_message = f'For some strange reason, {len(chapters) - len(scanlation_group)} more chapters have been ' \
                          f'scraped for groups for serie {serie_id}. Display might be wrong.'
    elif len(chapters) < len(scanlation_groups):
        warning_message = f'For some strange reason, {len(chapters) - len(scanlation_group)} more groups have been ' \
                          f'scraped for chapters for serie {serie_id}. Display might be wrong.'
    max_index = max(len(chapters), len(scanlation_groups))
    result_queue.put(
        ScrappedReleases(
            serie_id,
            chapters_releases=[ChapterRelease(chapter, group)
                               for chapter, group in zip(chapters[:max_index], scanlation_groups[:max_index])],
            warning_message=warning_message))
