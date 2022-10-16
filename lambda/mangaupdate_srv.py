from datetime import date, datetime
from collections import defaultdict
import urllib.parse
from typing import List, Dict, Set

import backoff
import requests

from logs import logger
from releases_types import SerieReleases, ChapterRelease, Serie


@backoff.on_exception(backoff.expo, requests.HTTPError, max_tries=3)
def _request_mangaupdate(page: int = 0) -> dict:
    requested_url = "https://api.mangaupdates.com/v1/releases/days"
    params = dict(include_metadata=True)
    if page != 0:
        params.update(page=page)
    requested_url += "?" + urllib.parse.urlencode(params)
    response = requests.get(requested_url)
    response.raise_for_status()
    return response.json()


def get_releases(until: date) -> List[SerieReleases]:
    """retrieves all the releases until a given date"""
    page = 0
    chapters_per_series: Dict[int, Set[ChapterRelease]] = defaultdict(set)
    while True:
        page_results = _request_mangaupdate(page=page)
        try:
            page_results = page_results["results"]
        except KeyError:
            logger.error(f"Unexpected page format on page {page}: {page_results}")
            raise

        min_release_dates = None
        for record in page_results:
            try:
                series_id = record["metadata"]["series"]["series_id"]
                chapter_data = record['record']
                chapter_release = ChapterRelease(
                    group=chapter_data["groups"][0]['name'],  # todo: get name of all groups
                    volume=chapter_data["volume"],
                    chapter=chapter_data["chapter"] if chapter_data["chapter"] is not None else '.',
                )
                release_date = datetime.strptime(chapter_data["release_date"], "%Y-%m-%d").date()
            except (KeyError, IndexError, ValueError):
                logger.error(f"Unexpected record format on page {page}: {record}")
                raise
            if min_release_dates is None or release_date < min_release_dates:
                min_release_dates = release_date
            if release_date >= until:
                chapters_per_series[series_id].add(chapter_release)
        if min_release_dates < until or min_release_dates is None:
            break
        page += 1
    return [SerieReleases(serie_id=str(series_id), chapters_releases=list(chapters))
            for series_id, chapters in chapters_per_series.items()]


@backoff.on_exception(backoff.expo, requests.HTTPError, max_tries=3)
def _request_serie(serie_id: int) -> dict:
    requested_url = f"https://api.mangaupdates.com/v1/series/{serie_id}"
    response = requests.get(requested_url)
    if response.status_code != 404:
        response.raise_for_status()
    else:
        raise ValueError(f"Serie id {serie_id} not found")
    return response.json()


def get_serie_info(serie_id: int) -> Serie:
    """return serie object along with serie """
    result = _request_serie(serie_id)
    try:
        return Serie(
            serie_id=str(result["series_id"]),
            serie_name=result["title"],
            img_url=result["image"]["url"]["original"]
        )
    except KeyError as e:
        raise KeyError(f"Failed to get key {str(e)} from record {result}.")


@backoff.on_exception(backoff.expo, requests.HTTPError, max_tries=3)
def search_series(keywords: str) -> List[Serie]:
    """Perform a search to try to find a given serie"""
    response = requests.post(
        "https://api.mangaupdates.com/v1/series/search",
        json=dict(
            search=keywords,
            perpage=20,
        ))
    response.raise_for_status()
    matching_series = []
    try:
        results = response.json()["results"]
    except KeyError as e:
        raise ValueError(f"Failed to get key {str(e)} from record {response.json()}.")
    for record in results:
        try:
            record = record['record']
            matching_series.append(
                Serie(
                    serie_id=str(record["series_id"]),
                    serie_name=record["title"],
                    img_url=record["image"]["url"]["original"]
                )
            )
        except KeyError as e:
            raise ValueError(f"Failed to get key {str(e)} from record {record}.")
    return matching_series


@backoff.on_exception(backoff.expo, requests.HTTPError, max_tries=3)
def get_image(url: str) -> bytes:
    response = requests.get(url)
    response.raise_for_status()
    return response.content
