import logging
from typing import Iterable, Union, List
import warnings

from bs4 import BeautifulSoup
import requests

from global_types import Chapter
from logs import logger
from page_marks_db import PageMark
from utils import flatmap


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


def _transform_page_to_beautiful_soup(url):
    try:
        bakaupdate_response = requests.get(url)
    except Exception as e:
        logger.error(f'failed to request {url}. Error {e}')
        raise e
    bakaupdate_response.raise_for_status()
    return BeautifulSoup(bakaupdate_response.content, features="lxml")


BASE_COL_CLASS_STR = "col-"
COLS_CLASSES = {BASE_COL_CLASS_STR + str(i) for i in range(1, 12 + 1)}


def _extract_rows_from_bootstrap(context_message: str, table_soup: BeautifulSoup)-> List[List[BeautifulSoup]]:
    """
    interprets bootstrap table as rows using div classes
    /!\ only 'col-<width_int>' format are supported
    /!\ table_soup should only have one level of bootstrap table
    /!\ table_soup elements should only be divs
    :raises LookupError in case the table is not understood
    """
    all_rows = []  # returned variable

    all_elems_in_table = table_soup.find_all('div')
    first_line_elem_index = next(iter(index for index, div in enumerate(all_elems_in_table)
                                      if not any('title' in css_class_elem for css_class_elem in div.get('class', []))), 0)

    logging.info(f'starting table rows at div {first_line_elem_index} out of : {len(all_elems_in_table)}.'
                 f' {all_elems_in_table[first_line_elem_index]}')

    # we have to reconstitute rows that are hidden within 'col-<width>' css style information in divs
    # for that we get each div and count the sum of divs until the accumulated div reaches 12

    # iteration initialisation
    row_cols_width_accumulator = 0
    row = []
    for div_index, div in enumerate(all_elems_in_table[first_line_elem_index:]):
        div_classes = div.get('class', [])

        # check if table is finished
        div_col_width = next(iter(class_[len(BASE_COL_CLASS_STR):] for class_ in div_classes if class_ in COLS_CLASSES), None)
        if div_col_width is None:  # line is not part of the table anymore
            logging.info(f'stopping scrapping at div {div_index} out of : {len(all_elems_in_table)}. Div : {div}.')
            break

        # add info to current row
        row.append(div)

        # check if row is finished
        div_col_width = int(div_col_width)  # should not fail due to cols_class filter
        row_cols_width_accumulator += div_col_width
        if row_cols_width_accumulator > 12:
            raise LookupError(f'Failed to scrap at div {div_index}. '
                              f'Retrieved row had {row_cols_width_accumulator} width instead of 12'
                              f'Latest div was {div}.')
        elif row_cols_width_accumulator == 12:
            all_rows.append(row)

            # prepare next iteration
            row = []
            row_cols_width_accumulator = 0
    return all_rows


VOL_COLUMN_INDEX = 2
CHAPTER_COLUMN_INDEX = 3
GROUPS_COLUMN_INDEX = 4

EXPECTED_ELEM_BY_LINE = 5

SPLITTING_CHAPTER_CHARS = ('+', '-')


def _scrap_rows_soups(context_message: str, rows_soups: Iterable[List[BeautifulSoup]]) -> List[ScrappedChapterRelease]:
    """ formats a row content to represent it as a ScrappedChapterRelease object"""
    scrapped_chapters = []
    for row_number, row_cells in enumerate(rows_soups):
        if len(row_cells) != EXPECTED_ELEM_BY_LINE:
            message = f"row {row_number} for {context_message} does not have 5 cells. Skipping it." \
                      f"\nRow was:\n {repr(row_cells)}"
            if len(row_cells) > 1:
                warnings.warn(message, ScrappingWarning)
            else:
                logging.info(message)
            continue

        volume_str = row_cells[VOL_COLUMN_INDEX].get_text()
        volume = None
        if volume_str.strip():
            try:
                volume = int(volume_str)
            except ValueError as e:
                warnings.warn(f"Failed to convert non empty volume str to int for {context_message}. Error was {e}",
                              ScrappingWarning)

        chapter_string = row_cells[CHAPTER_COLUMN_INDEX].get_text()

        group = row_cells[GROUPS_COLUMN_INDEX].get_text()
        chapters_elements = [chapter_string]
        for splitting_chars in SPLITTING_CHAPTER_CHARS:
            chapters_elements = flatmap(lambda elem: elem.split(splitting_chars), chapters_elements)
        # no interpolation as inference rule is too complex to code as of now given the diversity of possibilities.

        scrapped_chapters.extend(ScrappedChapterRelease(group, chapter, volume) for chapter in chapters_elements)
    return scrapped_chapters


def scrap_bakaupdate_releases(serie_id: str) -> ScrappedReleases:
    """ master function that scraps data from bakaupdate for releases. """
    url = f'https://www.mangaupdates.com/releases.html?search={serie_id}&stype=series'
    bakaupdate_soup = _transform_page_to_beautiful_soup(url)
    context_message = f'serie id {serie_id}'
    content_container = bakaupdate_soup.find('div', id=lambda x: x == 'main_content')
    table_soup = content_container.find_all('div', class_='row')[1]
    rows_soups = _extract_rows_from_bootstrap(context_message, table_soup)
    all_scrapped_chapter_release = _scrap_rows_soups(context_message, rows_soups)
    return ScrappedReleases(serie_id, all_scrapped_chapter_release)


def scrap_bakaupdate_serie(serie_id: str, serie_name: str=None, serie_img: str=None) -> PageMark:
    # always requests bakaupdate to check if the serie id is correct
    bakaupdate_soup = _transform_page_to_beautiful_soup(f'https://www.mangaupdates.com/series.html?id={serie_id}')
    if serie_img is None:
        serie_img = bakaupdate_soup.find('img', src=lambda url: "mangaupdates.com/image/" in url)['src']
    if serie_name is None:
        serie_name = bakaupdate_soup.find('span', class_="releasestitle tabletitle").get_text()
    return PageMark(serie_id=serie_id, serie_name=serie_name, img_link=serie_img)

