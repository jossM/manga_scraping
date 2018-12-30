from concurrent.futures import ThreadPoolExecutor, TimeoutError
from typing import List

import click

import emailing
from logs import logger
import page_marks_db
import skraper
import release_formating


def _scrap_and_format(page_mark: page_marks_db.PageMark) -> release_formating.FormattedScrappedReleases:
    """  mapped functions that scraps bkupdate and formats eventual new releases """
    logger.debug(f'scraping {page_mark}')
    scrapped_releases = skraper.scrap_bakaupdate_releases(page_mark.serie_id)
    formatted_scrapped_releases = release_formating.format_new_releases(scrapped_releases, page_mark)
    logger.debug(f'finished scraping {page_mark}')
    return formatted_scrapped_releases


def handle_scheduled_scraping(event, context):
    """ main function. """
    updated_serie_releases: List[release_formating.FormattedScrappedReleases] = []
    # scraping
    page_marks = page_marks_db.get_all()

    # why 3 ... because it's a thread, so GIL apply, and it's more than 1 while not being too high
    pool = ThreadPoolExecutor(max_workers=3)
    try:
        updated_serie_releases: List[release_formating.FormattedScrappedReleases] = \
            list(pool.map(_scrap_and_format, page_marks, timeout=600))
    except TimeoutError as e:  # catches scrap_stream timeout that are raised when calling next in for iterator
        missed_serie_page_marks = \
            {pm.serie_id for pm in page_marks} - {release.serie_id for release in updated_serie_releases}
        if not missed_serie_page_marks:
            error_message = f'Got a time out on serie scraping but no serie is missing. Timeout exception : {e}'
            logger.warning(error_message, exc_info=True)
        else:
            error_message = ('Scraping timed out before the handling of the following series  : '
                             f'{missed_serie_page_marks}. Exception : {e}')
            logger.error(error_message, exc_info=True)
    logger.info(f'End of scrapping for all series.')

    updated_serie_releases = [serie for serie in updated_serie_releases if serie.releases]

    # send email
    html_mail = emailing.helper.build_html_body(updated_serie_releases, len(page_marks))
    txt_mail = emailing.helper.build_txt_body(updated_serie_releases)
    emailing.helper.send_newsletter(text_body=txt_mail, html_body=html_mail)

    if not updated_serie_releases:
        logger.info('nothing to send. Stopping lambda.')
        return
    logger.info(f'Finaly over, registering : \n{updated_serie_releases}')

    # store updates
    page_marks_map = {pm.serie_id: pm for pm in page_marks}
    for releases in updated_serie_releases:
        if releases.serie_id not in page_marks_map:
            logger.error(f'For some strange reason serie {releases.serie_id} is present but absent from releases.')
            continue
        page_marks_map[releases.serie_id].extend(releases.releases)
    page_marks_db.batch_put(page_marks)


@click.command()
@click.argument('serie_id')
@click.option('--name', default=None, help='The name of the serie you want displayed.')
@click.option('--img', default=None, help='The image of the serie you want displayed.')
@click.option('--keep_chapters/--delete_chapters', default=True, help='Whether to keep the chapters already present in db.')
def add_serie_in_db(serie_id, name=None, img=None, keep_chapters=True):
    """ called only in local for admin tasks """
    new_page_mark = None
    if keep_chapters:
        new_page_mark = page_marks_db.get(serie_id)
        click.echo(f"retrieved {new_page_mark}")
        if new_page_mark is not None:
            if name is not None:
                new_page_mark.serie_name = name
            if img is not None:
                new_page_mark.img_link = img
    if new_page_mark is None:
        new_page_mark = skraper.scrap_bakaupdate_serie(serie_id, name, img)
    click.echo(f"stored {new_page_mark}")
    page_marks_db.put(new_page_mark)


if __name__ == "__main__":
    ## called only in local for admin tasks
    add_serie_in_db()
