from datetime import date, datetime
from collections import defaultdict
import urllib.parse
from typing import List, Dict, Set

import backoff
import requests

from logs import logger
from releases_types import SerieReleases, ChapterRelease


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
