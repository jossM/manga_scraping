from contextlib import closing
from multiprocessing import pool, cpu_count
from typing import Iterator
import warnings
import queue

from dynamo.page_marks_db import PageMark
from skraper import scrap_bakaupdate, ScrappedReleases


def to_yielder(q: queue.Queue, max_number_result: int, timeout: int) -> Iterator[ScrappedReleases]:
    for _ in range(max_number_result):
        try:
            yield q.get(block=True, timeout=timeout)
        except queue.Empty:
            return


def handler_scheduled_scraping(event, context):
    mail_message = MailMessage()

    # scraping
    with warnings.catch_warnings(record=True) as triggered_warning:
        page_marks = PageMark.get_all()
        result_queue = queue.Queue()
        with closing(pool.Pool(cpu_count()-1)) as request_pool:
            request_pool.map(scrap_bakaupdate, [(result_queue, page_mark.serie_id) for page_mark in page_marks])
        mail_message.add_warnings(triggered_warning)

    # compering to reading state
    page_marks_map = {page_mark.serie_id: page_mark for page_mark in page_marks}
    scrap_stream = to_yielder(result_queue, max_number_result=len(page_marks), timeout=10)
    for scrapped_releases in scrap_stream:
        if not scrapped_releases.releases:
            continue
        previous_page_marks = page_marks_map[scrapped_releases.serie_id]
        mail_message.add_releases(
            serie_name=previous_page_marks.serie_name,
            releases=[complete_release_info(release) for release in scrapped_releases.releases
                      if release not in previous_page_marks.chapter_marks])  # todo: add hashing to chapter
    # send mail
    mail_str = mail_message.build()
    send_to_sns(mail_str)
