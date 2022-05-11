from movie_object import MovieObject, MovieResult
import requests
import const


def api_query(name: str, result_type: str = 'movie', page: int = 1) -> MovieResult:
    r = requests.get(url='https://www.omdbapi.com/', params={'apikey': const.API_KEY,
                                                             's': name, 'page': page,
                                                             'type': result_type}).json()
    if r.get('Response') == 'False':
        raise RuntimeError(r['Error'])

    to_return: MovieResult = MovieResult(total=int(r['totalResults']), movies=list())
    for item in r['Search']:
        to_return.movies.append(MovieObject(title=item['Title'], year=item['Year'], imdb_id=item['imdbID'],
                                            poster=item['Poster']))
    return to_return


if __name__ == '__main__':
    try:
        print(api_query(name='Descend').movies[0].poster_url)
    except RuntimeError as e:
        print(e)
