from typing import List


class MovieObject:
    def __init__(self, title: str, year: str, imdb_id: str, poster: str):
        self.title: str = title
        self.year: str = year
        if self.year.endswith('–'):
            self.year = self.year[:-1]
        self.imdb_id: str = imdb_id
        self.poster_url: str = poster


class MovieResult:
    def __init__(self, total: int, movies: List[MovieObject]):
        self.total: int = total
        self.movies: List[MovieObject] = movies
        self.pages: int = (total // 10) + 1
