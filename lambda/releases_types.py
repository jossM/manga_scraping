from typing import Union, Iterable, NamedTuple

from global_types import Chapter


class Serie(NamedTuple):
    """ALl data stored concerning a given manga serie"""
    serie_id: str    # bakaupdate serie id
    serie_name: str  # Name of the serie on the page
    img_file: str    # Path to the file

    def as_dict(self):
        return self._asdict()


class ChapterRelease(Chapter):
    """ data on a given chapter """
    def __init__(self, group: str, chapter: str, volume: Union[int, None]= None):
        super(ChapterRelease, self).__init__(chapter, volume)
        self.group = group


class SerieReleases:
    """ data returned from scrapping """
    def __init__(self,
                 serie_id: str,
                 chapters_releases: Iterable[ChapterRelease]):
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
