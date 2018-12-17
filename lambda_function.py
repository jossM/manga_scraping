from concurrent.futures import ThreadPoolExecutor, TimeoutError
from datetime import datetime
from typing import List, Set
import warnings

from config import ERROR_FLAG
import emailing
from logs import logger
from page_marks_db import PageMark
import skraper
import release_formating


def handler_scheduled_scraping(event, context):
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
                print(scrapped_releases)
                if scrapped_releases.serie_id not in page_marks_map:
                    error_message = ('inconsistent execution :\n'
                                     f'serie id {scrapped_releases.serie_id} was present in scrap stream '
                                     f'but this value is missing from DB')
                    warnings.warn(f'{ERROR_FLAG} {error_message}')
                    logger.error(error_message)
                    # avoid raising to still send the mail with the warning
                    continue
                serie_page_mark: PageMark = page_marks_map[scrapped_releases.serie_id]
                if not scrapped_releases:
                    continue
                formatted_scrapped_new_releases = release_formating.filter_and_format_releases(
                    scrapped_releases.releases, serie_page_mark)
                if not formatted_scrapped_new_releases:
                    continue
                updated_serie_releases.append(formatted_scrapped_new_releases)
                serie_page_mark\
                    .extend(formatted_scrapped_new_releases.releases)\
                    .update(latest_update=datetime.now())
                scrapped_serie_page_marks.add(serie_page_mark)
        except TimeoutError as e:  # catches scrap_stream timeout that are raised when calling next in for iterator
            missed_serie_page_marks = set(page_marks) - scrapped_serie_page_marks
            if not missed_serie_page_marks:
                error_message = 'Got a time out on serie scraping but no serie is missing. Timeout exception :' + str(e)
                warnings.warn(error_message)
                logger.warning(error_message)
            else:
                error_message = (f'Scraping timed out before the handling of the following series  : '
                                 f'{missed_serie_page_marks}. Exception : ' + str(e))
                warnings.warn(error_message)
                logger.warning(error_message)
        triggered_warnings = list(catched_triggered_warnings)
        logger.info(f'End of scrapping for all series.')

    if not triggered_warnings and not updated_serie_releases:
        logger.info('nothing to send. Stopping lambda ')
        return
    elif updated_serie_releases:
        logger.info(f'scrapped_series :\n'
                    + '\n'.join(f'{serie.serie_name} (id: {serie.serie_id})' for serie in scrapped_serie_page_marks))
    else:
        logger.info(f'No scrapped_series to send. Sending warnings.')
    print(f'finaly over, registering\n{scrapped_serie_page_marks}')
    print(f'releases were : \n{updated_serie_releases}')

    html_mail = emailing.helper.build_html_body(updated_serie_releases, triggered_warnings, len(page_marks))
    txt_mail = emailing.helper.build_txt_body(updated_serie_releases, triggered_warnings)
    emailing.helper.send_newsletter(text_body=txt_mail, html_body=html_mail)
    # PageMark.batch_put(scrapped_serie_page_marks)
    return html_mail, txt_mail
