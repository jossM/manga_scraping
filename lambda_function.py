from concurrent.futures import ThreadPoolExecutor, TimeoutError
from datetime import datetime
from typing import List, Set
import uuid
import warnings

from config import ERROR_FLAG
import emailing
from logs import logger
from page_marks_db import PageMark
import skraper
import release_formating


def handler_scheduled_scraping(event, context):
    uid_str = uuid.uuid4().hex
    updated_serie_releases: List[release_formating.FormattedScrappedReleases] = []
    # scraping
    with warnings.catch_warnings(record=True) as catched_triggered_warnings:
        page_marks = PageMark.get_all()
        page_marks_map = {page_mark.serie_id: page_mark for page_mark in page_marks}

        # why 3 ... because it's a thread, so GIL apply, and it's more than 1 while not being too high
        pool = ThreadPoolExecutor(max_workers=3)
        scrap_stream = pool.map(skraper.scrap_bakaupdate, [page_mark.serie_id for page_mark in page_marks], timeout=60)
        scrapped_serie_page_marks: Set[PageMark] = set()
        try:
            for scrapped_releases in scrap_stream:
                if scrapped_releases.serie_id not in page_marks_map:
                    warnings.warn(f'{ERROR_FLAG} inconsistent execution :\n'
                                  f'serie id {scrapped_releases.serie_id} was present in scrap stream '
                                  f'but this value is missing from DB')
                    # avoid raising to still send the mail with the warning
                    continue
                serie_page_mark: PageMark = page_marks_map[scrapped_releases.serie_id]
                if not scrapped_releases:
                    continue
                formatted_scrapped_new_releases = release_formating.filter_and_format_releases(
                    scrapped_releases.releases, serie_page_mark)
                if formatted_scrapped_new_releases:
                    continue
                updated_serie_releases.append(formatted_scrapped_new_releases)
                serie_page_mark\
                    .extend(formatted_scrapped_new_releases.releases)\
                    .update(latest_update=datetime.now())
                scrapped_serie_page_marks.add(serie_page_mark)
        except TimeoutError as e:  # catches scrap_stream timeout that are raised when calling next in for iterator
            missed_serie_page_marks = set(page_marks) - scrapped_serie_page_marks
            if not missed_serie_page_marks:
                warnings.warn('Got a time out on serie scraping but no serie is missing. ' + str(e))
            else:
                warnings.warn(f'Scraping of the following series timed out : {missed_serie_page_marks}. ' + str(e))
        triggered_warnings = list(catched_triggered_warnings)
        logger.info(f'{uid_str}-End of scrapping .')
        for triggered_warning in triggered_warnings:
            logger.warning(f'{uid_str}-', triggered_warning)

    if not triggered_warnings and not updated_serie_releases:
        logger.info('nothing to send.')
    elif updated_serie_releases:
        logger.info(f'{uid_str}-scrapped_series :\n'
                    + '\n'.join(serie.serie_name for serie in scrapped_serie_page_marks))
        return
    html_mail_body = emailing.helper.build_html_body(updated_serie_releases, triggered_warnings)
    html_txt_body = emailing.helper.build_txt_body(updated_serie_releases, triggered_warnings)
    date_str = datetime.now().strftime("%a %d-%b")
    emailing.helper.send(f'Manga Newsletter - {date_str}', html_mail_body, html_txt_body)  # send mail
    PageMark.put_multi(scrapped_serie_page_marks)
