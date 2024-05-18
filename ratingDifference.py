import pandas as pd
import requests
from bs4 import BeautifulSoup, SoupStrainer
import time
from functions import getAverageRating

numResults = 12

df = pd.read_csv('movies.csv')
pagesPerFilm = 72
requestsSession = requests.Session()
starsToInt = { # Maps stars ('★★★½') to a number (3.5)
    "½": 0.5,
    "★": 1,
    "★½": 1.5,
    "★★": 2,
    "★★½": 2.5,
    "★★★": 3,
    "★★★½": 3.5,
    "★★★★": 4,
    "★★★★½": 4.5,
    "★★★★★": 5,
}
intToStars = { # Maps a number (3.5) to stars ('★★★½') 
    0.5: '½',
    1: '★',
    1.5: '★½',
    2: '★★',
    2.5: '★★½',
    3: '★★★',
    3.5: '★★★½',
    4: '★★★★',
    4.5: '★★★★½',
    5: '★★★★★'
}

    
def ceilDiv(a, b):
  return -(a // -b)

def getNumberMoviesWatched(username):
    response = requestsSession.get(f"https://letterboxd.com/{username}/")
    soup = BeautifulSoup(response.text, "lxml")
    first_h4 = soup.find('h4', class_='profile-statistic')
    span_value = first_h4.find('span', class_='value')
    text_inside_span = span_value.get_text()
    numMovies = int(''.join(c for c in text_inside_span if c.isdigit()))
    return numMovies

def getRatingsforUser(username): # gets the ratings for a user
  result = {}
  numPages = ceilDiv(getNumberMoviesWatched(username), pagesPerFilm)
  baseURL = f"https://letterboxd.com/{username}/films/by/entry-rating/page/"
  for pageNumber in range(1, numPages + 1):
    response = requestsSession.get(f"{baseURL}/{pageNumber}")
    if response.status_code == 200:
      poster_containers = BeautifulSoup(response.text, "html.parser", parse_only= SoupStrainer("li", class_="poster-container"))

      if poster_containers:
        for container in poster_containers:
          filmID = container.find(
              "div", class_="really-lazy-load").get("data-film-slug")
          ratingElement = container.find("span", class_="rating")
          if not ratingElement: # continues until movie doesn't have a rating, meaning there are no more movies with ratings
            return result
          rating = float(starsToInt[ratingElement.text.strip()])
          result[filmID] = rating
        pageNumber += 1
        
  return result

t = time.time()
userRatings = getRatingsforUser('UphazT')
print(f"Getting {len(userRatings)} ratings took {time.time() - t} seconds")
movies = []
t = time.time()
for filmID, rating in userRatings.items():
    avgRating = getAverageRating(filmID)
    movie = {}
    if avgRating:
        movie['filmID'] = filmID
        movie['avgRating'] = avgRating
        movie['userRating'] = rating
        movies.append(movie)
print(f"Parsing {len(userRatings)} ratings took {time.time() - t} seconds")


sortedFilms = sorted(movies, key=lambda x: x['userRating'] - x['avgRating'])
print()
print('Rated higher than average')
for film in reversed(sortedFilms[-numResults:]):
    print()
    print(f"{film['filmID']}: {intToStars[film['userRating']]} vs {film['avgRating']}")
print()
print()
print('Rated lower than average')
for film in sortedFilms[:numResults]:
    print()
    print(f"{film['filmID']}: {intToStars[film['userRating']]} vs {film['avgRating']}")