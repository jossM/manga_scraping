from page_marks_db import PageMark
from skraper.page_soup_srv import transform_page_to_beautiful_soup
from skraper.soup_extracter_lgq import extract_rows_from_bootstrap, scrap_rows_soups
from skraper.types import ScrappedReleases


def scrap_bakaupdate_releases(serie_id: str) -> ScrappedReleases:
    """ master function that scraps data from bakaupdate for releases. """
    url = f'https://www.mangaupdates.com/releases.html?search={serie_id}&stype=series'
    bakaupdate_soup = transform_page_to_beautiful_soup(url)
    context_message = f'serie id {serie_id}'
    content_container = bakaupdate_soup.find('div', id=lambda x: x == 'main_content')
    table_soup = content_container.find_all('div', class_='row')[1]
    rows_soups = extract_rows_from_bootstrap(context_message, table_soup)
    all_scrapped_chapter_release = scrap_rows_soups(context_message, rows_soups)
    return ScrappedReleases(serie_id, all_scrapped_chapter_release)


def scrap_bakaupdate_serie(serie_id: str, serie_name: str=None, serie_img: str=None) -> PageMark:
    # always requests bakaupdate to check if the serie id is correct
    bakaupdate_soup = transform_page_to_beautiful_soup(f'https://www.mangaupdates.com/series.html?id={serie_id}')
    if serie_img is None:
        serie_img = bakaupdate_soup.find('img', src=lambda url: "mangaupdates.com/image/" in url)['src']
    if serie_name is None:
        serie_name = bakaupdate_soup.find('span', class_="releasestitle tabletitle").get_text()
    return PageMark(serie_id=serie_id, serie_name=serie_name, img_link=serie_img)

