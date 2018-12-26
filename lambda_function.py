from concurrent.futures import ThreadPoolExecutor, TimeoutError
from typing import List
import warnings

import emailing
from logs import logger
import page_marks_db
import skraper
import release_formating


def scrap_and_format(page_mark: page_marks_db.PageMark) -> release_formating.FormattedScrappedReleases:
    """  mapped functions that scraps bkupdate and formats eventual new releases """
    scrapped_releases = skraper.scrap_bakaupdate(page_mark.serie_id)
    formatted_scrapped_releases = release_formating.format_new_releases(scrapped_releases, page_mark)
    return formatted_scrapped_releases


def handler_scheduled_scraping(event, context):
    """ main function. """
    updated_serie_releases: List[release_formating.FormattedScrappedReleases] = []
    # scraping
    with warnings.catch_warnings(record=True) as catched_triggered_warnings:
        page_marks = page_marks_db.get_all()

        # why 3 ... because it's a thread, so GIL apply, and it's more than 1 while not being too high
        pool = ThreadPoolExecutor(max_workers=3)
        try:
            updated_serie_releases: List[release_formating.FormattedScrappedReleases] = \
                list(pool.map(scrap_and_format, page_marks, timeout=600))
        except TimeoutError as e:  # catches scrap_stream timeout that are raised when calling next in for iterator
            missed_serie_page_marks = \
                {pm.serie_id for pm in page_marks} - {release.serie_id for release in updated_serie_releases}
            if not missed_serie_page_marks:
                error_message = f'Got a time out on serie scraping but no serie is missing. Timeout exception : {e}'
                warnings.warn(error_message)
                logger.warning(error_message, exc_info=True)
            else:
                error_message = ('Scraping timed out before the handling of the following series  : '
                                 f'{missed_serie_page_marks}. Exception : {e}')
                warnings.warn(error_message)
                logger.error(error_message, exc_info=True)
        triggered_warnings = list(catched_triggered_warnings)
        logger.info(f'End of scrapping for all series.')

    if not triggered_warnings and not updated_serie_releases:
        logger.info('nothing to send. Stopping lambda.')
        return
    else:
        logger.info(f'No scrapped_series to send. Sending warnings.')
    logger.info(f'finaly over, registering : \n{updated_serie_releases}')

    html_mail = emailing.helper.build_html_body(updated_serie_releases, triggered_warnings, len(page_marks))
    txt_mail = emailing.helper.build_txt_body(updated_serie_releases, triggered_warnings)
    emailing.helper.send_newsletter(text_body=txt_mail, html_body=html_mail)

    page_marks_map = {pm.serie_id: pm for pm in page_marks}
    for releases in updated_serie_releases:
        if releases.serie_id not in page_marks_map:
            logger.error(f'For some strange reason serie {releases.serie_id} is present but absent from releases.')
            continue
        page_marks_map[releases.serie_id].extend(releases.releases)
    # page_marks_db.batch_put(page_marks)
