from concurrent.futures import ThreadPoolExecutor, TimeoutError
import warnings

from config import ERROR_FLAG
from dynamo import page_marks_db
import skraper
import release_formating


def handler_scheduled_scraping(event, context):
    mail_message = MailMessage()

    # scraping
    with warnings.catch_warnings(record=True) as triggered_warning:
        page_marks = page_marks_db.PageMark.get_all()
        page_marks_map = {page_mark.serie_id: page_mark for page_mark in page_marks}

        pool = ThreadPoolExecutor(max_workers=3) # why 3 ... because it's a thread so GIL apply it's more than 1 and not too high
        scrap_stream = pool.map(skraper.scrap_bakaupdate, [page_mark.serie_id for page_mark in page_marks], timeout=60)
        try:
            scraped_serie_ids = set()
            for scrapped_releases in scrap_stream:
                scraped_serie_ids.add(scrapped_releases.serie_id)
                if not scrapped_releases.serie_id in page_marks_map:
                    warnings.warn(f'{ERROR_FLAG} inconsistent execution :\n'
                                  f'serie id {scrapped_releases.serie_id} was present in scrap stream '
                                  f'but this value is missing from DB')
                    # avoid raising to still send the mail with the warning
                    continue
                serie_page_mark = page_marks_map[scrapped_releases.serie_id]
                if not scrapped_releases.releases:
                    continue
                new_releases = sorted([release for release in scrapped_releases
                                       if release not in serie_page_mark.chapter_mark],
                                      reverse= True)
                if not new_releases:
                    continue
                new_releases_with_link = [release_formating._add_likely_link(previous_page_marks.serie_name, release)
                                          for release in new_releases]
                mail_message.add_releases(serie_name=previous_page_marks.serie_name, releases=new_releases_with_link)
        except TimeoutError:  # catches scrap_stream timeout that are raised when calling next in for iterator
            pass  # todo

        mail_message.add_warnings(triggered_warning)




    # send mail
    html_mail_str = mail_message.make_html()
    send_to_sns(html_mail_str)
