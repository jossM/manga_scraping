import copy
import os
import traceback
from typing import Union, Iterable
import warnings

from apiclient import discovery

from config import ERROR_FLAG
from global_types import Chapter
from skraper import ScrappedChapterRelease, ScrappedReleases

class FormattingWarning(Warning):
    """ Any issue during formatting of release will have this type """
    pass

class FormattedScrappedChapterRelease(ScrappedChapterRelease):
    """ data to be displayed for a single release """
    def __init__(self,
                 scraped_chapter_release: ScrappedChapterRelease,
                 top: bool = False,
                 url_release_link: Union[None, str] = None):
        super(FormattedScrappedChapterRelease, self).__init__(**{var: getattr(scraped_chapter_release, var)
                                                          for var in vars(scraped_chapter_release)})
        self.link = url_release_link
        self.top = top


class FormattedScrappedReleases(ScrappedReleases):
    """ data to be displayed for a serie """
    def __init__(self,
                 serie_id: str,
                 serie_html_title: str,
                 serie_img_link: str,
                 chapters_releases: Iterable[FormattedScrappedChapterRelease]):
        super(FormattedScrappedReleases, self).__init__(serie_id, chapters_releases)
        self.serie_html_title = serie_html_title
        self.serie_img_link = serie_img_link


google_customsearch_service = discovery.build("customsearch", "v1", developerKey=os.environ.get('CSE_MANGA_PERSO_KEY'))


def _add_likely_link(serie_name: str, release: Union[ScrappedChapterRelease, FormattedScrappedChapterRelease]) -> FormattedScrappedChapterRelease:
    """ Performs a query on a google custom search and adds the first hit as potential link.
     If no relevant is found, set link to None"""
    cse = google_customsearch_service.cse()
    exception_traceback = None
    search_responce = {}
    if isinstance(release, ScrappedChapterRelease):
        result = FormattedScrappedChapterRelease(release)
    else:
        result = copy.deepcopy(release)
    for attempt in range(5):
        try:
            search_responce = cse\
                .list(q=f'manga {serie_name} {release.group}',
                      cx=os.environ.get('CSE_MANGA_PERSO_ID'),
                      exactTerms=str(release.chapter),
                      safe='off',
                      siteSearchFilter='e', # exclusion of following site
                      siteSearch='www.mangaupdates.com')\
                .execute()
            exception_traceback = None
        except:
            exception_traceback = traceback.format_exc()
    if exception_traceback is not None:
        warnings.warn(f'{ERROR_FLAG}\n{exception_traceback}')
        return result
    if not search_responce or not search_responce.get('items', []):
        return FormattedScrappedChapterRelease(release)
    first_item = search_responce['items'][0]
    result.link = first_item.get('link', None)
    return result


def _get_top_releases(scraped_releases: Iterable[ScrappedChapterRelease],
                      chapters_page_mark: Iterable[Chapter],
                      max_chapter_limit: int= 5) -> Iterable[ScrappedChapterRelease]:
    """ returns releases that are 'hot' as defined by previous page mark chapter and max_chapter_limit"""
    chapters_page_mark = sorted(chapters_page_mark, reverse=True)
    limiting_chapter = chapters_page_mark[-min(len(chapters_page_mark), max_chapter_limit)]
    for release in scraped_releases:
        if not release > limiting_chapter:
            continue
        yield release


def format_release(scrapped_releases: ScrappedReleases) -> FormattedScrappedReleases:
    pass # todo:
