import base64
from typing import Tuple, Dict

import backoff
from bs4 import BeautifulSoup
import requests

from logs import logger

HOST = 'www.mangaupdates.com'


def base_headers():
    return {
        'Host': HOST,
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:79.0) Gecko/20100101 Firefox/79.0',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }


def build_serie_url(serie_id: str) -> str:
    return f'https://www.mangaupdates.com/releases.html?search={serie_id}&stype=series'


@backoff.on_exception(backoff.expo, requests.HTTPError, max_tries=3)
def transform_page_to_beautiful_soup(url: str) -> Tuple[BeautifulSoup, Dict[str, str]]:
    """ request a web page and transforms it to a beautiful soup object"""
    try:
        bakaupdate_response = requests.get(
            url,
            headers=base_headers().update({
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            })
        )
    except Exception as e:
        logger.error(f'Failed to request {url}. Error {e}')
        raise e
    bakaupdate_response.raise_for_status()
    return BeautifulSoup(bakaupdate_response.content, features="lxml"), bakaupdate_response.cookies.get_dict()


@backoff.on_exception(backoff.expo, requests.HTTPError, max_tries=3)
def retrieve_img(referer: str, url: str, cookies: Dict[str, str]) -> str:
    """ retrieves the img in a local file and stop there """
    img_response = requests.get(
        url,
        headers=base_headers().update({
            'Accept': 'image/webp,image/jpeg',
            'Referer': referer,
            'Cookie': '; '.join(f"{key}={value}" for key, value in cookies.items()),
            'Pragma': 'no-cache',
            'Cache-Control': 'no-cache'
        }),
        cookies=cookies)
    img_response.raise_for_status()
    image_format = img_response.headers.get('content-type', '').split('/')[-1]
    local_img_path = f"/tmp/scrapped_img_{base64.b64encode(url.split(HOST)[-1].strip('/'))}.{image_format}"
    with open(local_img_path, 'wb') as img_file:
        img_file.write(img_response.content)
    return local_img_path
