import logging
from datetime import datetime, timedelta
from typing import List

import pytz

import emailing
import page_marks_db
import release_formating
from logs import logger
from mangaupdate_srv import get_releases


def handle_scheduled_scraping(event, context):
    """ main function on lambda. """
    # scraping
    all_page_marks = page_marks_db.get_all()
    page_marks_map = {pm.serie_id: pm for pm in all_page_marks}
    # sort to update first the oldest values and then the most recent.
    all_series_releases = get_releases((datetime.now() - timedelta(days=2)).date())
    logger.info(f'Got info for all series.')
    updated_serie_releases: List[release_formating.FormattedSerieReleases] = []
    for serie_releases in all_series_releases:
        if serie_releases.serie_id not in page_marks_map:
            logger.info(f"skipping {serie_releases} as it is not watched")
            continue
        formatted_scrapped_releases = release_formating.format_new_releases(
            serie_releases=serie_releases,
            serie_page_mark=page_marks_map[serie_releases.serie_id],
        )
        if formatted_scrapped_releases.releases:
            updated_serie_releases.append(formatted_scrapped_releases)
        else:
            logger.info(f"Skipping {serie_releases} as it has already been reported.")
    # send email
    html_mail = emailing.helper.build_html_body(updated_serie_releases, len(all_page_marks))
    txt_mail = emailing.helper.build_txt_body(updated_serie_releases)
    emailing.helper.send_newsletter(text_body=txt_mail, html_body=html_mail)

    if not updated_serie_releases:
        logger.info('nothing to store. Stopping lambda.')
        return
    all_releases = '\n'.join(sorted([f'\t{r.serie_id}, {r.serie_title}' for r in updated_serie_releases]))
    logger.info(f'Finaly over, registering : \n{all_releases}')

    # store updates

    for releases in updated_serie_releases:
        if releases.serie_id not in page_marks_map:
            logger.error(f'For some strange reason serie {releases.serie_id} is present but absent from releases.')
            continue
        logger.info(f'adding {len(releases.releases)} to {releases.serie_id}, {releases.serie_title}')
        page_mark = page_marks_map[releases.serie_id]
        page_mark.extend(releases.releases)
        page_mark.latest_update = datetime.utcnow()
        page_mark.latest_update.replace(tzinfo=pytz.utc)

    page_marks_db.batch_put(all_page_marks)
