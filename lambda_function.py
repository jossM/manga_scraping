from contextlib import closing
from multiprocessing import pool, cpu_count
from typing import Iterator
import queue

from skraper import scrap_bakaupdate, ScrappedReleases


def to_yielder(q: queue.Queue, max_number_result: int, timeout: int) -> Iterator[ScrappedReleases]:
    for _ in range(max_number_result):
        try:
            yield q.get(block=True, timeout=timeout)
        except queue.Empty:
            return


def handler_scheduled_scraping(event, context):
    page_marks = scan_dynamo_db() # todo
    result_queue = queue.Queue()
    with closing(pool.Pool(cpu_count()-1)) as request_pool:
        request_pool.map(scrap_bakaupdate, [(result_queue, page_mark.serie_id) for page_mark in page_marks])
    page_marks_map = {page_mark.serie_id: page_mark for page_mark in page_marks}
    scrap_stream = to_yielder(result_queue,
                              max_number_result=len(page_marks),
                              timeout=10)
    mail_message = MailMessage()
    for scrapped_releases in scrap_stream:
        if scrapped_releases.warning:
            mail_message.add_warning(scrapped_releases.warning_message)
        latest_chapter_release = scrapped_releases.latest_chapter_release
        if latest_chapter_release is None:
            continue
        page_mark = page_marks_map[scrapped_releases.serie_id]
        if latest_chapter_release.chapter > page_mark.latest_read_chapter:
            expected_chapter_link = get_lucky_google_link(page_mark.serie_name,
                                                          latest_chapter_release.group,
                                                          latest_chapter_release.chapter)
            mail_message.add_release(
                serie_name=page_mark.serie_name,
                group=latest_chapter_release.group,
                chapter_link=expected_chapter_link)
    send_to_sns(mail_message)