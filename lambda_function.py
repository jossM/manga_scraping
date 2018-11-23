from concurrent.futures import ThreadPoolExecutor, TimeoutError
from typing import List, Set
import warnings

from config import ERROR_FLAG
import emailing
import page_marks_db
import skraper
import release_formating


def handler_scheduled_scraping(event, context):
    updated_serie_releases: List[release_formating.FormattedScrappedReleases] = []
    # scraping
    with warnings.catch_warnings(record=True) as catched_triggered_warnings:
        page_marks = page_marks_db.PageMark.get_all()
        page_marks_map = {page_mark.serie_id: page_mark for page_mark in page_marks}

        # why 3 ... because it's a thread so GIL apply it's more than 1 and not too high
        pool = ThreadPoolExecutor(max_workers=3)
        scrap_stream = pool.map(skraper.scrap_bakaupdate, [page_mark.serie_id for page_mark in page_marks], timeout=60)
        scraped_serie_ids: Set[str] = set()
        try:
            for scrapped_releases in scrap_stream:
                if not scrapped_releases.serie_id in page_marks_map:
                    warnings.warn(f'{ERROR_FLAG} inconsistent execution :\n'
                                  f'serie id {scrapped_releases.serie_id} was present in scrap stream '
                                  f'but this value is missing from DB')
                    # avoid raising to still send the mail with the warning
                    continue
                if not scrapped_releases:
                    continue
                formatted_scrapped_new_releases = release_formating.filter_and_format_releases(
                    scrapped_releases.releases, page_marks_map[scrapped_releases.serie_id])
                if formatted_scrapped_new_releases:
                    continue
                updated_serie_releases.append(formatted_scrapped_new_releases)
                scraped_serie_ids.add(scrapped_releases.serie_id)
        except TimeoutError:  # catches scrap_stream timeout that are raised when calling next in for iterator
            pass  # todo

        triggered_warnings = list(catched_triggered_warnings)
        html_mail_body = emailing.build_email_body(updated_serie_releases, triggered_warnings)
    emailing.send_to_sns(html_mail_body) # send mail
