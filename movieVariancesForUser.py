import heapq
import argparse

from main import getRatingsforUser, loadRatingsFomFile, calculateVariance

VARIANCE_DECIMALS = 3

def parseArguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("username")
    args = parser.parse_args()
    return args.username

def updateMovie(moviesVariance, variance, movieTitle, movieID, userRating):
    index_to_insert = 0
    while index_to_insert < len(moviesVariance) and variance < moviesVariance[index_to_insert][1]:
        index_to_insert += 1
    
    # Insert the new movie at the appropriate position
    moviesVariance.insert(index_to_insert, [movieTitle, variance, movieID, userRating])
    if len(moviesVariance) > numberOfMovies:
        moviesVariance.pop()


FILM_CACHE_FILE = "film_cache.pickle"
filmCache = loadRatingsFomFile(FILM_CACHE_FILE)
username = parseArguments()

try:
  userRatings = getRatingsforUser(username) # tries to get ratings for given user
except Exception as e: # catches any exceptions
  print(f"An error occurred while trying to get ratings for {username}: {e}")
  exit(1) 

numberOfMovies = 20
moviesVariance = []


for movie in userRatings:
    movieID, movieTitle, userRating = movie
    if movieID in filmCache:
        avgRating = filmCache[movieID]['average']
        variance = calculateVariance(filmCache[movieID], userRating, avgRating)
        if len(moviesVariance) < numberOfMovies or variance > moviesVariance[-1][1]:
            updateMovie(moviesVariance, variance, movieTitle, movieID, userRating)

count = 1
for title, var, filmID, userRating in moviesVariance:
    print(f"{count}. {username} rated {title} {userRating} stars")
    print(f"↪ https://letterboxd.com/film/{filmID}/")
    count += 1
print()