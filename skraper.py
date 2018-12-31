from typing import Iterable, Union
import warnings

from bs4 import BeautifulSoup
import requests

from global_types import Chapter
from page_marks_db import PageMark
from logs import logger


class ScrappingWarning(UserWarning):
    """ Any issue during scraping will have this type """
    pass


class ScrappedChapterRelease(Chapter):
    """ data on a given chapter """
    def __init__(self, group: str, chapter: str, volume: Union[int, None]= None):
        super(ScrappedChapterRelease, self).__init__(chapter, volume)
        self.group = group


class ScrappedReleases:
    """ data returned from scrapping """
    def __init__(self,
                 serie_id: str,
                 chapters_releases: Iterable[ScrappedChapterRelease]):
        self.serie_id = serie_id
        self.releases = sorted(chapters_releases, reverse=True)

    def __iter__(self):
        for chapter_release in self.releases:
            yield chapter_release

    def __repr__(self) -> str:
        rep = f"Available releases for serie {self.serie_id}:"
        releases = '\n'.join(f"{release} \tby group {release.group}" for release in self.releases)
        if releases:
            rep += '\n' + releases
        return rep


def _transform_page_to_beautiful_soup(url: str) -> BeautifulSoup:
    try:
        bakaupdate_response = requests.get(url)
    except Exception as e:
        logger.error(f'failed to request {url}. Error {e}')
        raise e
    bakaupdate_response.raise_for_status()
    return BeautifulSoup(bakaupdate_response.content, features="lxml")


def scrap_bakaupdate_releases(serie_id: str) -> ScrappedReleases:
    """
    Scraps data from bakaupdate for releases.
    Function to be executed in a thread to avoid waiting.
    """
    bakaupdate_soup = _transform_page_to_beautiful_soup(
        f'https://www.mangaupdates.com/releases.html?search={serie_id}&stype=series')
    content_table_container = bakaupdate_soup.find('td', id=lambda x: x == 'main_content')
    inner_tables = content_table_container.find_all('table')
    inner_tables.sort(key=lambda table_soup: len(table_soup))
    content_table = inner_tables[-1]

    context_message = f'serie id {serie_id}'
    scrapped_chapters = []
    for row_number, row in enumerate(content_table.find_all('tr')):
        row_cells = tuple(row.find_all('td', **{'class': lambda class_value: class_value == 'text pad'}))
        if not row_cells:
            continue
        if len(row_cells) != 5:
            message = (f"row {row_number} for {context_message} does not have 5 cells\n "
                       f"Row was:\n {repr(row)}")
            warnings.warn(message, ScrappingWarning)
            logger.error(message)
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


def scrap_bakaupdate_serie(serie_id: str, serie_name: str=None, serie_img: str=None) -> PageMark:
    # always requests bakaupdate to check if the serie id is correct
    bakaupdate_soup = _transform_page_to_beautiful_soup(f'https://www.mangaupdates.com/series.html?id={serie_id}')
    if serie_img is None:
        serie_img = bakaupdate_soup.find('img', src=lambda url: "mangaupdates.com/image/" in url)['src']
    if serie_name is None:
        serie_name = bakaupdate_soup.find('span', class_="releasestitle tabletitle").get_text()
    return PageMark(serie_id=serie_id, serie_name=serie_name, img_link=serie_img)

