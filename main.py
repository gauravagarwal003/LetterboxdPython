import pickle
import argparse
import re
import time
from tqdm import tqdm
from bs4 import BeautifulSoup
import requests

starsToInt = {
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
}  # Maps stars ('★★★½') to a number (3.5)
MIN_MOVIES = 30 # minimum number of films user must rate to be considered
MAX_LEADERBOARD_SIZE = 1000 # how many users will be shown on leadeboard
MIN_TOTAL_RATINGS =  500 # minimum number of ratings a film must have to be considered
FILM_CACHE_FILE = "film_cache.pickle"
LEADERBOARD_FILE = "leaderboard.pickle"
PRINT_STATS_FILE = "stats.txt"
PRINT_LEADERBOARD_FILE = "leaderboard.txt"


def parseArgument():
    parser = argparse.ArgumentParser()
    parser.add_argument("username")
    args = parser.parse_args()
    return args.username

def calculateVariance(filmInfo, userRating, avgRating):
    histogramVariance = (filmInfo['Total'] - filmInfo[f"{userRating} stars"]) / (filmInfo['Total'] - 1)
    simpleVariance = abs(avgRating - userRating)
    return histogramVariance * simpleVariance

def getTopFromLeaderboard(leaderboard):
  return leaderboard[:MAX_LEADERBOARD_SIZE]  # gets top users from leaderboard

def loadLeaderboardFromFile(filename):
  try:
    with open(filename, "rb") as file:
      leaderboard = pickle.load(file)
  except FileNotFoundError:
    leaderboard = []
  return leaderboard  # loads leaderboard


def saveLeaderboardToFile(leaderboard, filename):
  with open(filename, "wb") as file:
    pickle.dump(leaderboard, file)


def updateLeaderboard(leaderboard, username, user_variance):
  for i, (variance, usr) in enumerate(leaderboard):
    if usr == username:
      leaderboard[i] = (user_variance, username)
      break
  else:
    leaderboard.append((user_variance, username))

  leaderboard.sort(reverse=True)

  return leaderboard


def loadRatingsFomFile(filename):
  try:
    with open(filename, "rb") as file:
      film_cache = pickle.load(file)
  except FileNotFoundError:
    film_cache = {}
  return film_cache  # load ratings


def saveRatingsToFile(film_cache, filename):
  with open(filename, "wb") as file:
    pickle.dump(film_cache, file)  # save ratings

def getRatingsforUser(username):
  baseURL = f"https://letterboxd.com/{username}/films/by/entry-rating/page/"
  pageNumber = 1
  pageHasFilms = True

  returnList = []

  while pageHasFilms:
    response = requests.get(f"{baseURL}/{pageNumber}")
    if response.status_code == 200:
      soup = BeautifulSoup(response.content, "html.parser")
      poster_containers = soup.find_all("li", class_="poster-container")

      if poster_containers:
        for container in poster_containers:
          filmID = container.find(
              "div", class_="really-lazy-load").get("data-film-slug")
          ratingElement = container.find("span", class_="rating")
          if not ratingElement:
            return returnList
          rating = ratingElement.text.strip()
          title = container.find("img", class_="image").get("alt")
          returnList.append([filmID, title, rating])

        pageNumber += 1
      else:
        pageHasFilms = False
    else:
      pageHasFilms = False
  return returnList

filmCache = loadRatingsFomFile(FILM_CACHE_FILE)
moviesInCacheBefore = len(filmCache)
username = parseArgument()
startTime = time.time()


try:
  data = getRatingsforUser(username)
except requests.exceptions.ConnectionError:
  print("Connection Error: Could not connect to the server.")
  exit(1) 
except requests.exceptions.Timeout:
  print("Timeout Error: The request timed out.")
  exit(1)
except requests.exceptions.TooManyRedirects:
  print("Too Many Redirects: The request exceeded the maximum number of redirects.")
  exit(1)
except requests.exceptions.HTTPError as e:
  print(f"HTTP Error: {e.response.status_code} - {e.response.reason}")
  exit(1)
except requests.exceptions.RequestException as e:
  print(f"Request Exception: {e}")
  exit(1)
except Exception as e:
  print(f"An unexpected error occurred: {e}")
  exit(1)


thisUserRatings = {}  # Maps movie ID ('dune-part-two') to user's rating (9)
with open(PRINT_STATS_FILE, "a") as output:
  output.write(f"\n")


totalVariance = 0
cacheHit = 0
validMovies = 0

for movie in tqdm(data, desc=username):  # find the user's ratings
    movieID, movieTitle, userRatingRaw = movie
    if userRatingRaw in starsToInt:  # Checks if user rated movie or not
        userRating = float(starsToInt[userRatingRaw])
        if movieID in filmCache:
            avgRating = float(filmCache[movieID]['average'])
            cacheHit += 1
            validMovies += 1
        else:
            response = requests.get(f"https://letterboxd.com/csi/film/{movieID}/rating-histogram/")
            html_string = response.content.decode('utf-8')
            soup = BeautifulSoup(html_string, 'html.parser')

            try:
                ratings_text = soup.find('a', {'class': 'tooltip', 'title': True}).get('title')
                totalRatings = int(ratings_text.split()[-2].replace(",", ""))
                avgRating = float(ratings_text.split()[3])
            except Exception as e: # checks if film is valid
                continue
            if avgRating is None or avgRating == 'None' or totalRatings < MIN_TOTAL_RATINGS:  # checks if film is valid
                continue
            
            # valid film at this point
            dict = {}
            dict['title'] = movieTitle
            avgRating = float(avgRating)
            dict['average'] = avgRating
            histogram = BeautifulSoup(response.content, "lxml").find_all("li", {"class": "rating-histogram-bar"})
            for i, r in enumerate(histogram):
                string = r.text.strip(" ")
                if string == "":
                    dict[f"{(i+1)/2} stars"] = 0
                else:
                    numRatings = re.findall(r"\d+", string)[:-1]
                    numRatings = int("".join(numRatings))
                    dict[f"{(i+1)/2} stars"] = numRatings
            dict["Total"] = totalRatings
            filmCache[movieID] = dict

            validMovies += 1

        totalVariance += calculateVariance(filmCache[movieID], userRating, avgRating)          

if validMovies < MIN_MOVIES:
  with open(PRINT_STATS_FILE, "a") as output:
    output.write(f"Not enough ratings for valid movies. {username} has rated {validMovies} valid movies.\n")
  exit()

with open(PRINT_STATS_FILE, "a") as output:
  output.write(f"Found {validMovies} valid ratings for {username}!\n")

  
print()
if validMovies != 0:
  avgVariance = totalVariance / validMovies
  leaderboard = loadLeaderboardFromFile(LEADERBOARD_FILE)
  leaderboard = updateLeaderboard(leaderboard, username, avgVariance)
  with open(PRINT_STATS_FILE, "a") as output:
    output.write("Cache hit: " + str(round(100 * cacheHit / validMovies, 2)) + "%")
    output.write('\n')
    output.write("Cache size: " + str(len(filmCache)) + " movies (" + str(len(filmCache) - moviesInCacheBefore) + " movies added to cache)" )
    output.write('\n')
    output.write(f"Total time taken: {round(time.time() - startTime, 2)} seconds")
    output.write('\n')

  count = 1
  with open(PRINT_LEADERBOARD_FILE, "w") as board:
    for var, currentUser in leaderboard:
      board.write(f"{count}. {currentUser}'s uniqueness is {round(var, 3)}\n")
      board.write(f"↪ https://letterboxd.com/{currentUser}/\n")
      count += 1

  with open(PRINT_STATS_FILE, "a") as output:
    output.write('\n')

saveRatingsToFile(filmCache, FILM_CACHE_FILE)
saveLeaderboardToFile(leaderboard, LEADERBOARD_FILE)
