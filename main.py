from datetime import datetime
from typing import List

import pytz

import emailing
from logs import logger
import page_marks_db
import skraper
import release_formating


def handle_scheduled_scraping(event, context):
    """ main function on lambda. """
    # scraping
    all_page_marks = page_marks_db.get_all()
    updated_serie_releases: List[release_formating.FormattedScrappedReleases] = []
    # sort to update first the oldest values and then the most recent.
    ordered_page_marks = [pm for pm in all_page_marks if pm.latest_update is None] + \
                         sorted([pm for pm in all_page_marks if pm.latest_update is not None],
                                reverse=True, key=lambda pm: pm.latest_update)
    updated_serie = 0
    for page_mark in ordered_page_marks:

        logger.debug(f'scraping {page_mark.serie_id}, {page_mark.serie_name}')
        try:
            scrapped_releases = skraper.scrap_bakaupdate_releases(page_mark.serie_id)
            formatted_scrapped_releases = release_formating.format_new_releases(scrapped_releases, page_mark)
            if formatted_scrapped_releases.releases:
                updated_serie_releases.append(formatted_scrapped_releases)
            page_mark.latest_update = datetime.utcnow()
            page_mark.latest_update.replace(tzinfo=pytz.utc)

        except Exception as e:
            logger.error(f'Failed scraping {page_mark.serie_id}, {page_mark.serie_name}. Error {e}')
        else:
            logger.debug(f'finished scrapping {page_mark.serie_id}, {page_mark.serie_name} ')
            updated_serie += 1
    logger.info(f'End of scrapping for all series.')

    # send email
    html_mail = emailing.helper.build_html_body(updated_serie_releases, updated_serie, len(all_page_marks))
    txt_mail = emailing.helper.build_txt_body(updated_serie_releases)
    emailing.helper.send_newsletter(text_body=txt_mail, html_body=html_mail)

    if not updated_serie_releases:
        logger.info('nothing to store. Stopping lambda.')
        return
    all_releases = '\n'.join(sorted([f'\t{r.serie_id}, {r.serie_title}' for r in updated_serie_releases]))
    logger.info(f'Finaly over, registering : \n{all_releases}')

    # store updates
    page_marks_map = {pm.serie_id: pm for pm in all_page_marks}
    for releases in updated_serie_releases:
        if releases.serie_id not in page_marks_map:
            logger.error(f'For some strange reason serie {releases.serie_id} is present but absent from releases.')
            continue
        logger.debug(f'adding {len(releases.releases)} to {releases.serie_id}, {releases.serie_title}')
        page_marks_map[releases.serie_id].extend(releases.releases)
    page_marks_db.batch_put(all_page_marks)
