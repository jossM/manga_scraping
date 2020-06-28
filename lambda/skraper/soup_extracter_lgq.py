import logging
import warnings
from typing import List, Iterable

from bs4 import BeautifulSoup

from skraper.types import ScrappingWarning, ScrappedChapterRelease
from utils import flatmap

BASE_COL_CLASS_STR = "col-"
COLS_CLASSES = {BASE_COL_CLASS_STR + str(i) for i in range(1, 12 + 1)}

VOL_COLUMN_INDEX = 2
CHAPTER_COLUMN_INDEX = 3
GROUPS_COLUMN_INDEX = 4
EXPECTED_ELEM_BY_LINE = 5
SPLITTING_CHAPTER_CHARS = ('+', '-')


def extract_rows_from_bootstrap(context_message: str, table_soup: BeautifulSoup)-> List[List[BeautifulSoup]]:
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

    logging.info(f'starting table rows at div {first_line_elem_index} out of : {len(all_elems_in_table)}'
                 f' for {context_message}. {all_elems_in_table[first_line_elem_index]}')

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
            logging.info(f'stopping scrapping at div {div_index} out of : {len(all_elems_in_table)} '
                         f'for {context_message}. Div : {div}.')
            break

        # add info to current row
        row.append(div)

        # check if row is finished
        div_col_width = int(div_col_width)  # should not fail due to cols_class filter
        row_cols_width_accumulator += div_col_width
        if row_cols_width_accumulator > 12:
            raise LookupError(f'Failed to scrap at div {div_index} for {context_message}.'
                              f'Retrieved row had {row_cols_width_accumulator} width instead of 12'
                              f'Latest div was {div}.')
        elif row_cols_width_accumulator == 12:
            all_rows.append(row)

            # prepare next iteration
            row = []
            row_cols_width_accumulator = 0
    return all_rows


def scrap_rows_soups(context_message: str, rows_soups: Iterable[List[BeautifulSoup]]) -> List[ScrappedChapterRelease]:
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