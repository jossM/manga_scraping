from skraper.bakaupdate_scrapping_srv import transform_page_to_beautiful_soup, retrieve_img, build_serie_url
from skraper.soup_extracter_lgq import extract_rows_from_bootstrap, scrap_rows_soups
from skraper.types import ScrappedReleases,ScrappedSerie


def scrap_bakaupdate_releases(serie_id: str) -> ScrappedReleases:
    """ master function that scraps data from bakaupdate for releases. """
    url = build_serie_url(serie_id)
    bakaupdate_soup, _ = transform_page_to_beautiful_soup(url)
    context_message = f'serie id {serie_id}'
    content_container = bakaupdate_soup.find('div', id=lambda x: x == 'main_content')
    table_soup = content_container.find_all('div', class_='row')[1]
    rows_soups = extract_rows_from_bootstrap(context_message, table_soup)
    all_scrapped_chapter_release = scrap_rows_soups(context_message, rows_soups)
    return ScrappedReleases(serie_id, all_scrapped_chapter_release)


def scrap_bakaupdate_serie(serie_id: str, serie_name: str=None) -> ScrappedSerie:
    # always requests bakaupdate to check if the serie id is correct
    serie_url = f'https://www.mangaupdates.com/series.html?id={serie_id}'
    bakaupdate_soup, cookies = transform_page_to_beautiful_soup(serie_url)
    if serie_name is None:
        serie_name = bakaupdate_soup.find('span', class_="releasestitle tabletitle").get_text()
    img_url = bakaupdate_soup.find('img', src=lambda url: "mangaupdates.com/image/" in url)['src']
    img_file_path = retrieve_img(referer=serie_url, url=img_url, cookies=cookies)
    return ScrappedSerie(serie_id=serie_id, serie_name=serie_name, img_file=img_file_path)

