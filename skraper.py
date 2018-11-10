from typing import Iterable, List
from queue import Queue
import warnings

from bs4 import BeautifulSoup
import requests

import chapter_type
from dynamo import page_marks_db


class ScrappingWarning(UserWarning):
    pass


class ScrappedReleases(object):
    """ represents data returned from scrapping """

    class ScrappedChapterRelease(chapter_type.Chapter):
        def __init__(self, chapter: str, group: str):
            super(ScrappedReleases.ScrappedChapterRelease, self).__init__(chapter)
            self.group = group

        @property
        def chapter(self):
            return self._chapter

    def __init__(self,
                 serie_id: str,
                 chapters_releases: Iterable[ScrappedChapterRelease],
                 warning_message=None,
                 observed_diff_between_chapter: float=None,
                 deduced: bool=False):
        self.serie_id = serie_id
        self.releases = sorted(chapters_releases)
        self.warning_message = warning_message
        if not self.releases:
            if not observed_diff_between_chapter:
                self.min_dif_between_chapter = 1.
            else:
                self.min_dif_between_chapter = observed_diff_between_chapter
        else:
            releases_diff = [self.releases[i + 1] - self.releases[i] for i in range(len(self.releases)-1)]
            self.min_dif_between_chapter = \
                min([observed_diff_between_chapter] + [diff for diff in releases_diff if diff])
        self.deduced = deduced

    def has_warning(self):
        return self.warning_message is not None

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


def scrap_bakaupdate(result_queue: Queue, serie_page_mark: page_marks_db.PageMark) -> None:
    """
    Scraps data from bakaupdate for releases.
    Function to be executed in a thread to avoid waiting.
    """
    bakaupdate_page = requests.get(f'https://www.mangaupdates.com/series.html?id={serie_page_mark.serie_id}')
    bakaupdate_soup = BeautifulSoup(bakaupdate_page.content, features="lxml")
    latest_release_title_soup = bakaupdate_soup.find(string='Latest Release(s)').parent.parent
    latest_release_div_soup = latest_release_title_soup.find_next_sibling()
    chapters = _extract_soup_data(latest_release_div_soup, 'i')
    scanlation_groups = _extract_soup_data(latest_release_div_soup, 'a')
    warning_message = ''
    if len(chapters) > len(scanlation_groups):
        warning_message = f'For some strange reason, {len(chapters) - len(scanlation_groups)} more chapters have been '\
                          f'scraped than for groups'
    elif len(chapters) < len(scanlation_groups):
        warning_message = f'For some strange reason, {len(chapters) - len(scanlation_groups)} more groups have been ' \
                          f'scraped than for chapters'

    max_index = max(len(chapters), len(scanlation_groups))
    chapter_release_info = list(zip(chapters[:max_index], scanlation_groups[:max_index]))
    chapter_release_info.sort(key=lambda zip_chapter: '-' in str(zip_chapter[0]))

    scrapped_chapters_releases = []
    for chapter, group in chapter_release_info:
        for split_chapter in chapter.split('-'):
            scrapped_chapters_releases.append(ScrappedReleases.ScrappedChapterRelease(split_chapter, group))

    if warning_message:
        warning_message += \
            f'</br>For serie : {serie_page_mark.serie_id}: display might be wrong. original display was : ' \
            f'</br><div>{latest_release_div_soup.prettify()}</div>'
        warnings.warn(warning_message, ScrappingWarning)
    result_queue.put(ScrappedReleases(serie_page_mark.serie_id, scrapped_chapters_releases, warning_message))
