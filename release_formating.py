import copy
import os
import traceback
from typing import Union, Iterable
import warnings

from apiclient import discovery

from config import ERROR_FLAG
from page_marks_db import PageMark
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
                 serie_title: str,
                 serie_img_link: str,
                 chapters_releases: Iterable[FormattedScrappedChapterRelease]):
        super(FormattedScrappedReleases, self).__init__(serie_id, chapters_releases)
        self.serie_title = serie_title
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
    if not search_responce or not search_responce.get('items', None):
        return FormattedScrappedChapterRelease(release)
    first_item = search_responce['items'][0]
    result.link = first_item.get('link', None)
    return result


def filter_and_format_releases(scrapped_releases: ScrappedReleases,
                               serie_page_mark: PageMark,
                               top_chapter_lim: int= 5
                               ) -> FormattedScrappedReleases:
    """ returns new releases with links and information of whether they are top chapters as defined by
     top_chapter_limit"""
    new_releases = sorted([release for release in scrapped_releases if release not in serie_page_mark.chapter_marks],
                          reverse=True)
    chapters_page_mark = sorted(serie_page_mark.chapter_marks, reverse=True)
    limiting_chapter = chapters_page_mark[-min(len(chapters_page_mark), top_chapter_lim)]
    formated_scrapped_new_chapter_release = [_add_likely_link(serie_page_mark.serie_name, release) for release in new_releases]
    for release in formated_scrapped_new_chapter_release:
        release.top = release > limiting_chapter
    return FormattedScrappedReleases(
        serie_id=serie_page_mark.serie_id,
        serie_html_title=serie_page_mark.serie_name,
        serie_img_link='',  #todo
        chapters_releases=formated_scrapped_new_chapter_release)
