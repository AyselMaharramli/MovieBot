from dataclasses import dataclass


@dataclass(frozen=True)
class Types:
    movie: str = 'movie'
    series: str = 'series'
    episode: str = 'episode'
