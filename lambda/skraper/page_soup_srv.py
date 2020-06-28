import requests
from bs4 import BeautifulSoup

from logs import logger


def transform_page_to_beautiful_soup(url: str) -> BeautifulSoup:
    """ request a web page and transforms it to a beautiful soup object"""
    try:
        bakaupdate_response = requests.get(url)
    except Exception as e:
        logger.error(f'failed to request {url}. Error {e}')
        raise e
    bakaupdate_response.raise_for_status()
    return BeautifulSoup(bakaupdate_response.content, features="lxml")