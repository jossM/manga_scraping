from typing import Iterable, List, Union
from queue import Queue
import warnings

from bs4 import BeautifulSoup
import requests

from chapter_type import Chapter


class ScrappingWarning(UserWarning):
    pass


class ScrappedReleases(object):
    """ represents data returned from scrapping """

    class ScrappedChapterRelease(Chapter):
        def __init__(self, chapter: str, group: str):
            super(ScrappedReleases.ScrappedChapterRelease, self).__init__(chapter)
            self.group = group

        @property
        def chapter(self):
            return self._chapter

    def __init__(self, serie_id: str, chapters_releases: Iterable[ScrappedChapterRelease], warning_message=None):
        self.serie_id = serie_id
        self.releases = sorted(chapters_releases, reverse=True)
        self.warning_message = warning_message

    @property
    def warning(self):
        return self.warning_message is not None

    @property
    def latest_chapter_release(self) -> Union[None, ScrappedChapterRelease]:
        if not self.releases:
            return None
        return self.releases[-1]

    def __repr__(self):
        rep = f"Available releases for serie {self.serie_id}:"
        releases = '\n'.join(f"chapter {release} by group {release.group}" for release in self.releases)
        if releases:
            rep += '\n' + releases
        if self.warning_message:
            rep += "\nWARNING : " + self.warning_message
        return rep


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
    bakaupdate_soup = BeautifulSoup(bakaupdate_page.content, features="lxml")
    latest_release_title_soup = bakaupdate_soup.find(string='Latest Release(s)').parent.parent
    latest_release_div_soup = latest_release_title_soup.find_next_sibling()
    chapters = _extract_soup_data(latest_release_div_soup, 'i')
    scanlation_groups = _extract_soup_data(latest_release_div_soup, 'a')
    warning_message = None
    if len(chapters) > len(scanlation_groups):
        warning_message = f'For some strange reason, {len(chapters) - len(scanlation_groups)} more chapters have been '\
                          f'scraped than for groups'
    elif len(chapters) < len(scanlation_groups):
        warning_message = f'For some strange reason, {len(chapters) - len(scanlation_groups)} more groups have been ' \
                          f'scraped than for chapters'
    if warning_message:
        warning_message += f'</br>For serie : {serie_id}: display might be wrong. original display was : </br>' \
                           f'<div>{latest_release_div_soup.prettify()}</div></br>'
        warnings.warn(warning_message,ScrappingWarning)

    max_index = max(len(chapters), len(scanlation_groups))
    result_queue.put(
        ScrappedReleases(
            serie_id=serie_id,
            chapters_releases=[ScrappedReleases.ScrappedChapterRelease(chapter, group)
                               for chapter, group in zip(chapters[:max_index], scanlation_groups[:max_index])],
            warning_message=warning_message))
