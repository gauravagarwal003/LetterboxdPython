import pickle
import argparse
import re
import time
from tqdm import tqdm
from bs4 import BeautifulSoup, SoupStrainer
import requests

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

MIN_MOVIES = 30 # minimum number of films user must rate to be considered
MAX_LEADERBOARD_SIZE = 1000 # how many users will be shown on leadeboard
MIN_TOTAL_RATINGS =  500 # minimum number of ratings a film must have to be considered
FILM_CACHE_FILE = "pickles/film_cache.pickle" # file where film info is stored
LEADERBOARD_FILE = "pickles/leaderboard.pickle" # file where leaderboard is stored
PRINT_STATS_FILE = "stats.txt" # file where stats are printed
PRINT_LEADERBOARD_FILE = "leaderboard.txt" # file where leaderboard is printed
VARIANCE_DECIMALS = 4 # number of decimal places to round variance to
STATS_DECIMALS = 2 # number of decimal places to round stats to

def parseArgument(): # Parses the username from the command line
    parser = argparse.ArgumentParser()
    parser.add_argument("username")
    args = parser.parse_args()
    return args.username

def calculateVariance(filmInfo, userRating, avgRating): # calculates the variance of a user's rating
    histogramVariance = (filmInfo['Total'] - filmInfo[f"{userRating} stars"]) / (filmInfo['Total'] - 1)
    simpleVariance = abs(avgRating - userRating)
    return histogramVariance * simpleVariance

def getTopFromLeaderboard(leaderboard): # gets the top users from the leaderboard
  return leaderboard[:MAX_LEADERBOARD_SIZE]

def loadLeaderboardFromFile(filename): # loads leaderboard
  try:
    with open(filename, "rb") as file:
      leaderboard = pickle.load(file)
  except FileNotFoundError:
    leaderboard = []
  return leaderboard  # loads leaderboard

def saveLeaderboardToFile(leaderboard, filename): # saves leaderboard
  with open(filename, "wb") as file:
    pickle.dump(leaderboard, file)

def updateLeaderboard(leaderboard, username, user_variance): # updates the leaderboard given a new user and variance
  for i, (variance, usr) in enumerate(leaderboard):
    if usr == username:
      leaderboard[i] = (user_variance, username)
      break
  else:
    leaderboard.append((user_variance, username))

  leaderboard.sort(reverse=True)

  return leaderboard

def loadRatingsFomFile(filename): # loads ratings
  try:
    with open(filename, "rb") as file:
      film_cache = pickle.load(file)
  except FileNotFoundError:
    film_cache = {}
  return film_cache  # load ratings

def saveRatingsToFile(film_cache, filename): # saves ratings
  with open(filename, "wb") as file:
    pickle.dump(film_cache, file)  # save ratings

def getRatingsforUser(username): # gets the ratings for a user
  baseURL = f"https://letterboxd.com/{username}/films/by/entry-rating/page/"
  pageNumber = 1
  pageHasFilms = True
  result = set()
  requestsSession = requests.Session()
  while pageHasFilms: # continues until there are no more films
    response = requestsSession.get(f"{baseURL}/{pageNumber}")
    if response.status_code == 200:
      poster_containers = BeautifulSoup(response.text, "lxml", parse_only= SoupStrainer("li", class_="poster-container"))

      if poster_containers:
        for container in poster_containers:
          filmID = container.find(
              "div", class_="really-lazy-load").get("data-film-slug")
          ratingElement = container.find("span", class_="rating")
          if not ratingElement: # continues until movie doesn't have a rating, meaning there are no more movies with ratings
            return result
          rating = float(starsToInt[ratingElement.text.strip()])
          title = container.find("img", class_="image").get("alt")
          result.add((filmID, title, rating))

        pageNumber += 1
      else:
        pageHasFilms = False
    else:
      pageHasFilms = False
  return result

filmCache = loadRatingsFomFile(FILM_CACHE_FILE) # stores film info in filmCache
moviesInCacheBefore = len(filmCache) # gets the number of movies in the cache before
username = parseArgument() # stores username from the command line in username
startTime = time.time() # stores the start time

try:
  userRatings = getRatingsforUser(username) # tries to get ratings for given user
except Exception as e: # catches any exceptions
  print(f"An error occurred while trying to get ratings for {username}: {e}")
  exit(1) 

with open(PRINT_STATS_FILE, "a") as output:
  output.write(f"\n")

totalVariance = 0
cacheHit = 0
validMovies = 0

if len(userRatings) < MIN_MOVIES: # checks if user has rated enough valid movies
  with open(PRINT_STATS_FILE, "a") as output:
    output.write(f"{username} has only rated {len(userRatings)} movies.\n")
  exit()

requestsSession = requests.Session()
for movie in tqdm(userRatings, desc = f"{username}"):  # go through user's ratings
    movieID, movieTitle, userRating = movie
    if movieID in filmCache: # checks if movie is in cache
        avgRating = filmCache[movieID]['average']
        cacheHit += 1
        validMovies += 1
      
    else: # movie not in cache
        response = requestsSession.get(f"https://letterboxd.com/csi/film/{movieID}/rating-histogram/")
        soup = BeautifulSoup(response.text, 'lxml')

        try: # try extracting the average ratings and total ratings
            ratingsText = soup.find('a', {'class': 'tooltip', 'title': True}).get('title')
            totalRatings = int(ratingsText.split()[-2].replace(",", ""))
            avgRating = float(ratingsText.split()[3])
        except Exception as e: # if there is an error, film is not valid and skip this film
            continue
        if avgRating is None or avgRating == 'None' or totalRatings < MIN_TOTAL_RATINGS:  # film is not valid and skip this film
            continue
        
        # valid film at this point
        dict = {}
        dict['title'] = movieTitle
        dict['average'] = avgRating
        dict["Total"] = totalRatings
        histogram = BeautifulSoup(response.text, "lxml", parse_only = SoupStrainer("li", class_="rating-histogram-bar")) # get histogram
        for i, r in enumerate(histogram): # go through histogram
            string = r.text.strip(" ")
            if string == "":
                dict[f"{(i+1)/2} stars"] = 0
            else:
                numRatings = re.findall(r"\d+", string)[:-1]
                numRatings = int("".join(numRatings))
                dict[f"{(i+1)/2} stars"] = numRatings

        filmCache[movieID] = dict # store film info in cache
        validMovies += 1

    totalVariance += calculateVariance(filmCache[movieID], userRating, avgRating) # add to total variance

if validMovies < MIN_MOVIES: # checks if user has rated enough valid movies
  with open(PRINT_STATS_FILE, "a") as output:
    output.write(f"{username} has only rated {validMovies} valid movies.\n")
  exit()

with open(PRINT_STATS_FILE, "a") as output: 
  output.write(f"Found {validMovies} valid ratings for {username}!\n")

  
print()

avgVariance = totalVariance / validMovies #calculate average variance
leaderboard = loadLeaderboardFromFile(LEADERBOARD_FILE) # loads leaderboard
leaderboard = updateLeaderboard(leaderboard, username, avgVariance) # updates leaderboard
with open(PRINT_STATS_FILE, "a") as output: # adds stats to stats file
  output.write("Cache hit: " + str(round(100 * cacheHit / validMovies, STATS_DECIMALS)) + "%")
  output.write('\n')
  output.write("Cache size: " + str(len(filmCache)) + " movies (" + str(len(filmCache) - moviesInCacheBefore) + " movies added to cache)" )
  output.write('\n')
  output.write(f"Total time taken: {round(time.time() - startTime, STATS_DECIMALS)} seconds")
  output.write('\n')

count = 1
with open(PRINT_LEADERBOARD_FILE, "w") as board: # rewrites leaderboard file
  for var, currentUser in leaderboard:
    board.write(f"{count}. {currentUser}'s uniqueness is {round(var, VARIANCE_DECIMALS)}\n")
    board.write(f"↪ https://letterboxd.com/{currentUser}/\n")
    count += 1

saveRatingsToFile(filmCache, FILM_CACHE_FILE)
saveLeaderboardToFile(leaderboard, LEADERBOARD_FILE)
