from typing import Union, Iterable
from urllib.parse import urlunparse, urlencode

from page_marks_db import PageMark
from skraper.types import ScrappedChapterRelease, ScrappedReleases


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


def add_likely_link(
        serie_name: str,
        release: Union[ScrappedChapterRelease, FormattedScrappedChapterRelease])\
        -> FormattedScrappedChapterRelease:

    if release.volume:
        query = f' v.{release.volume} '
    else:
        query = ""
    query += f'"{release.chapter}" manga {serie_name} {release.group} -site:mangaupdates.com -site:play.google.com'
    google_url = urlunparse(('https',
                             'www.google.com',
                             '/search',
                             None,
                             urlencode(dict(
                                 q=query,
                                 safe='images',  # remove safe search
                                 btnG="Search",
                                 lr="lang_en",)),
                             None))
    release.link = google_url
    return release


def format_new_releases(scrapped_releases: ScrappedReleases,
                        serie_page_mark: PageMark,
                        top_chapter_lim: int= 5) -> FormattedScrappedReleases:
    """ returns new releases with links and information of whether they are top chapters as defined by
     top_chapter_limit"""
    new_releases = sorted([release for release in scrapped_releases if release not in serie_page_mark.chapter_marks],
                          reverse=True)
    chapters_page_mark = sorted(serie_page_mark.chapter_marks, reverse=True)
    if chapters_page_mark:
        limiting_chapter = chapters_page_mark[-min(len(chapters_page_mark), top_chapter_lim)]

        def is_top(release):
            return release > limiting_chapter
    else:

        def is_top(_):
            return True
    formatted_scrapped_new_chapter_release = []
    for release in new_releases:
        formatted_release = add_likely_link(serie_page_mark.serie_name, release)
        formatted_release.top = is_top(release)
        formatted_scrapped_new_chapter_release.append(formatted_release)
    return FormattedScrappedReleases(
        serie_id=serie_page_mark.serie_id,
        serie_title=serie_page_mark.serie_name,
        serie_img_link=serie_page_mark.img_link,
        chapters_releases=formatted_scrapped_new_chapter_release)
