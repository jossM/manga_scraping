from contextlib import closing
from multiprocessing import pool, cpu_count
from typing import Iterator
import warnings
import queue

from dynamo import page_marks_db
import skraper
import web_search


def to_yielder(q: queue.Queue, max_number_result: int, timeout: int) -> Iterator[skraper.ScrappedReleases]:
    for _ in range(max_number_result):
        try:
            yield q.get(block=True, timeout=timeout)
        except queue.Empty:
            return


def handler_scheduled_scraping(event, context):
    mail_message = MailMessage()

    # scraping
    with warnings.catch_warnings(record=True) as triggered_warning:
        page_marks = page_marks_db.PageMark.get_all()
        result_queue = queue.Queue()
        with closing(pool.Pool(cpu_count()-1)) as request_pool:
            request_pool.map(skraper.scrap_bakaupdate, [(result_queue, page_mark) for page_mark in page_marks])
        mail_message.add_warnings(triggered_warning)

    # compering to reading state
    page_marks_map = {page_mark.serie_id: page_mark for page_mark in page_marks}
    scrap_stream = to_yielder(result_queue, max_number_result=len(page_marks), timeout=10)
    for scrapped_releases in scrap_stream:
        if not scrapped_releases.releases:
            continue
        previous_page_marks = page_marks_map[scrapped_releases.serie_id]
        new_releases = [release for release in page_marks_map[scrapped_releases.serie_id].releases
                        if release not in previous_page_marks.chapter_marks]
        if not new_releases:
            continue
        new_releases_with_link = [web_search.add_likely_link(previous_page_marks.serie_name, release)
                                  for release in new_releases]
        mail_message.add_releases(serie_name=previous_page_marks.serie_name, releases=new_releases_with_link)
    # send mail
    html_mail_str = mail_message.make_html()
    send_to_sns(html_mail_str)
