from collections import Sequence
from typing import Iterable, Union
import warnings

from bs4 import BeautifulSoup
import requests

import global_types


class ScrappingWarning(UserWarning):
    """ Any issue during scraping will have this type """
    pass


class ScrappedChapterRelease(global_types.Chapter):
    """ data on a given chapter """
    def __init__(self, group: str, chapter: str, volume: Union[int, None]= None):
        super(ScrappedChapterRelease, self).__init__(chapter, volume)
        self.group = group


class ScrappedReleases(Sequence):
    """ data returned from scrapping """
    def __init__(self,
                 serie_id: str,
                 chapters_releases: Iterable[ScrappedChapterRelease]):
        self.serie_id = serie_id
        self.releases = sorted(chapters_releases, reverse=True)

    def __getitem__(self, item: int) -> ScrappedChapterRelease:
        try:
            return self.releases[item]
        except IndexError:
            raise TypeError(f'trying to access element number {item} while there are only {len(self)} element(s)')
        except TypeError as e:
            raise TypeError(str(e).replace('list', 'ScrappedReleases', count=1))

    def __len__(self) -> int:
        return len(self.releases)

    def __repr__(self) -> str:
        rep = f"Available releases for serie {self.serie_id}:"
        releases = '\n'.join(f"{release} \tby group {release.group}" for release in self.releases)
        if releases:
            rep += '\n' + releases
        return rep


def scrap_bakaupdate(serie_id: str) -> ScrappedReleases:
    """
    Scraps data from bakaupdate for releases.
    Function to be executed in a thread to avoid waiting.
    """
    context_message = f'serie id {serie_id}'
    bakaupdate_page = requests.get(
        f'https://www.mangaupdates.com/releases.html?search={serie_id}&stype=series')
    bakaupdate_soup = BeautifulSoup(bakaupdate_page.content, features="lxml")
    content_table_container = bakaupdate_soup.find('td', id=lambda x: x == 'main_content')
    inner_tables = content_table_container.find_all('table')
    inner_tables.sort(key=lambda table_soup: len(table_soup))
    content_table = inner_tables[-1]
    scrapped_chapters = []
    for row_number, row in enumerate(content_table.find_all('tr')):
        row_cells = tuple(row.find_all('td', **{'class': lambda class_value: class_value == 'text pad'}))
        if not row_cells:
            continue
        if len(row_cells) != 5:
            warnings.warn(f"row {row_number} for {context_message} does not have 5 cells\n "
                          f"Row was:\n {repr(row)}",
                          ScrappingWarning)
            continue
        try:
            volume = int(row_cells[2].get_text())
        except ValueError:
            volume = None
        chapter_string = row_cells[3].get_text()

        group = row_cells[4].get_text()

        for chapters_elements in chapter_string.split('+'):
            if '-' in chapters_elements:
                chapters = chapters_elements.split('-')
            else:
                chapters = [chapters_elements]
            scrapped_chapters.extend(ScrappedChapterRelease(group, chapter, volume)
                                     for chapter in chapters)
            # no interpolation as inference rule is too complex to code as of now given the diversity of possibilities.
    return ScrappedReleases(serie_id, scrapped_chapters)
