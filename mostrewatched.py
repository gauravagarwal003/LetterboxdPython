from bs4 import BeautifulSoup
import requests
import argparse


from main import getRatingsforUser, loadRatingsFomFile, calculateVariance

VARIANCE_DECIMALS = 3

def parseArguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("username")
    args = parser.parse_args()
    return args.username

FILM_CACHE_FILE = "film_cache.pickle"
filmCache = loadRatingsFomFile(FILM_CACHE_FILE)
username = parseArguments()

baseURL = f"https://letterboxd.com/{username}/films/diary/page"
pageNumber = 1
pageHasFilms = True
result = {}

while pageHasFilms:
  response = requests.get(f"{baseURL}/{pageNumber}")
  if response.status_code == 200:
    soup = BeautifulSoup(response.content, "html.parser")
    tbody = soup.find('tbody')
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

# Sort the filtered dictionary by values in descending order
sorted_filtered_dict = dict(
    sorted(filtered_dict.items(), key=lambda item: item[1], reverse=True))

# Print the sorted dictionary
for key, value in sorted_filtered_dict.items():
  result = filmCache.get(key)
  if result:
    print(result['title'], ":", value)
  else:
    print(key, ":", value)

  
