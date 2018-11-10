from apiclient import discovery
import os

from skraper import ScrappedReleases


class ScrappedReleasesWithLink(ScrappedReleases.ScrappedChapterRelease):
    def __init__(self, link, **kwargs):
        self.link = link
        super(ScrappedReleasesWithLink, self).__init__(**kwargs)


google_customsearch_service = discovery.build("customsearch", "v1", developerKey=os.environ.get('CSE_MANGA_PERSO_KEY'))


def add_likely_link(serie_name: str, release: ScrappedReleases.ScrappedChapterRelease) -> ScrappedReleasesWithLink:
    cse = google_customsearch_service.cse()
    search_responce = cse.list(q=f'manga {serie_name} {release.group}',
                               cx=os.environ.get('CSE_MANGA_PERSO_ID'),
                               exactTerms=release.chapter,
                               safe='off',
                               siteSearchFilter='e',
                               siteSearch='www.mangaupdates.com').execute()

