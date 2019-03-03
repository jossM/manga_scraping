from typing import Union, Iterable

from global_types import Chapter


class ScrappingWarning(UserWarning):
    """ Any issue during scraping will have this type """
    pass


class ScrappedChapterRelease(Chapter):
    """ data on a given chapter """
    def __init__(self, group: str, chapter: str, volume: Union[int, None]= None):
        super(ScrappedChapterRelease, self).__init__(chapter, volume)
        self.group = group


class ScrappedReleases:
    """ data returned from scrapping """
    def __init__(self,
                 serie_id: str,
                 chapters_releases: Iterable[ScrappedChapterRelease]):
        self.serie_id = serie_id
        self.releases = sorted(chapters_releases, reverse=True)

    def __iter__(self):
        for chapter_release in self.releases:
            yield chapter_release

    def __repr__(self) -> str:
        rep = f"Available releases for serie {self.serie_id}:"
        releases = '\n'.join(f"{release} \tby group {release.group}" for release in self.releases)
        if releases:
            rep += '\n' + releases
        return rep