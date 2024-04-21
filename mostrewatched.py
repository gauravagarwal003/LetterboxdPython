from bs4 import BeautifulSoup, SoupStrainer
import requests
import argparse
import time
import pickle

def loadRatingsFomFile(filename): # loads ratings
  try:
    with open(filename, "rb") as file:
      film_cache = pickle.load(file)
  except FileNotFoundError:
    film_cache = {}
  return film_cache 

def parseArguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("username")
    args = parser.parse_args()
    return args.username

def checkIfUserExists(username):
  response = requestsSession.get(f"https://letterboxd.com/{username}/")
  if response.status_code == 200:
    return True
  else:
    return False

start_time = time.time()
FILM_CACHE_FILE = "pickles/film_cache.pickle"
filmCache = loadRatingsFomFile(FILM_CACHE_FILE)
username = parseArguments()

baseURL = f"https://letterboxd.com/{username}/films/diary/page"
pageNumber = 1
pageHasFilms = True
result = {}
requestsSession = requests.Session()

while pageHasFilms:
  response = requestsSession.get(f"{baseURL}/{pageNumber}")
  if response.status_code == 200:
    tbody = BeautifulSoup(response.text, "lxml", parse_only = SoupStrainer("tbody"))
      
    if tbody:
      tr_with_class = tbody.find_all('tr', class_=True)
      if tr_with_class:
        tr_elements = tbody.find_all('tr')

        for tr in tr_elements:
          td_film_details = tr.find('td', class_='td-film-details')

          if td_film_details:
            div_film_slug = td_film_details.find('div',
                                                {'data-film-slug': True})

            if div_film_slug:
              film_slug = div_film_slug['data-film-slug']
              if film_slug in result:
                result[film_slug] += 1
              else:
                result[film_slug] = 1
        pageNumber += 1
      else:
        pageHasFilms = False
    else:
      pageHasFilms = False
  else:
    pageHasFilms = False

filtered_dict = {key: value for key, value in result.items() if value > 1}
sorted_filtered_dict = dict(
    sorted(filtered_dict.items(), key=lambda item: item[1], reverse=True))
  
print("--- %s seconds ---" % (time.time() - start_time))
