import pandas as pd
import os
import requests
import json
from bs4 import BeautifulSoup, SoupStrainer
import time
from functions import *

CSV_FILE_NAME = "movies.csv"
ERROR_FILE_NAME = "error.txt"
STATS_FILE_NAME = "stats.txt"
LAST_PAGE_FILE_NAME = "last_page.txt"
minViews = 20000

try:
    tryToOpen = pd.read_csv(CSV_FILE_NAME)        
except (pd.errors.EmptyDataError, FileNotFoundError):
    with open(CSV_FILE_NAME, 'w') as file:
        file.write("movieID,title,avgRating,year,numTotalRatings,numReviews,num0_5StarRatings,num1StarRatings,num1_5StarRatings,num2StarRatings,num2_5StarRatings,num3StarRatings,num3_5StarRatings,num4StarRatings,num4_5StarRatings,num5StarRatings,director,numViews,numLikes,numFans,genres,themes,nanoGenres,runtime,primaryLanguage,spokenLanguages,countries,numListAppearances,cast,producers,writers,cinematography,editors,studios,posterLink,imdbLink,backdropLink, dateCreated" + '\n')
pagesPerFilm = 72
requestsSession = requests.Session()

starsToInt = { # Maps stars ('★★★½') to a string ('3_5')
    "half-★": '0_5',
    "★": '1',
    "★½": '1_5',
    "★★": '2',
    "★★½": '2_5',
    "★★★": '3',
    "★★★½": '3_5',
    "★★★★": '4',
    "★★★★½": '4_5',
    "★★★★★": '5',
}

def getMoviesWatchedForUser(username):
  numPages = ceilDiv(getNumberMoviesWatched(username), pagesPerFilm)
  baseURL = f"https://letterboxd.com/{username}/films/by/entry-rating/page/"
  result = []
  for pageNumber in range(1, numPages + 1):
    response = requestsSession.get(f"{baseURL}/{pageNumber}")
    strainer = SoupStrainer("li", class_="poster-container")
    poster_containers = BeautifulSoup(response.text,
                                      "html.parser",
                                      parse_only=strainer)
    for container in poster_containers:
      filmID = container.find("div",
                              class_="really-lazy-load").get("data-film-slug")
      result.append((filmID))
  return result
    
def addMovieToDatabase(movieID):
    if isMovieInDatabase(movieID, CSV_FILE_NAME):
        return False
    
    response = requestsSession.get(f"https://letterboxd.com/film/{movieID}/details")
    responseLikes = requestsSession.get(f"https://letterboxd.com/film/{movieID}/likes")
        
    soup = BeautifulSoup(response.text, 'lxml')
    soupLikes = BeautifulSoup(responseLikes.text, 'lxml')

    # check if movie satisfies minimum views
    if getnumViews(True, movieID, soup = soupLikes) < minViews:
        return False
        
    # check if movie is a TV show or miniseries (according to TMDB link)
    if not isMovie(movieID, soup = soup):
        return False
    
    responseThemes = requestsSession.get(f"https://letterboxd.com/film/{movieID}/themes")
    responseNanoGenres = requestsSession.get(f"https://letterboxd.com/film/{movieID}/nanogenres")
    responseCrew = requestsSession.get(f"https://letterboxd.com/film/{movieID}/crew")

    soupThemes = BeautifulSoup(responseThemes.text, 'lxml')
    soupNanoGenres = BeautifulSoup(responseNanoGenres.text, 'lxml')
    soupCrew = BeautifulSoup(responseCrew.text, 'lxml')

    data = {}
    
    # add movie id
    data['movieID'] = movieID 
    
    # add title
    data['title'] = getTitle(movieID, soup = soup)
    
    # add average rating
    data['avgRating'] = getAverageRating(True, movieID)
    
    # add year
    data['year'] = getReleaseYear(movieID, soup = soup)

    scriptTag = soup.find('script', type='application/ld+json')
    if scriptTag:
        json_content = scriptTag.string
        start_index = json_content.find('/* <![CDATA[ */') + len('/* <![CDATA[ */')
        end_index = json_content.find('/* ]]> */')
        json_data = json_content[start_index:end_index].strip()
        jsonData = json.loads(json_data)
            
    # add total ratings and number of reviews
    data['numTotalRatings'] = None
    data['numReviews'] = None  
    if scriptTag:
        data['numReviews'] = getNumReviews(True, movieID, jsonData = jsonData)
        data['numTotalRatings'] = getNumRatings(True, movieID, jsonData = jsonData)

    histogram = getHistogram(True, movieID)
    index = 0
    for rating in starsToInt.values(): 
        data[f"num{rating}StarRatings"] = histogram[index]
        index += 1
    
    # add director(s)
    data['director'] = []
    if scriptTag:
        data['director'] = getDirectors(movieID, jsonData = jsonData)
    
    # add views
    data['numViews'] = getnumViews(True, movieID, soup = soupLikes)
    
    # add likes
    data['numLikes'] = getNumLikes(True, movieID, soup = soupLikes)
        
    # add fans
    data['numFans'] = getNumFans(True,  movieID, soup = soupLikes)
    
    #add genre(s)
    data['genres'] = []
    if scriptTag:
        data['genres'] = getGenres(movieID, jsonData = jsonData)
                
    # add themes
    data['themes'] = getThemes(movieID, soup = soupThemes)
                    
    # add nanogenres
    data['nanoGenres'] = getNanoGenres(movieID, soup = soupNanoGenres)
    
    # add runtime
    data['runtime'] = getRuntime(movieID, soup = soup)
        
    # add primary and secondary languages
    data['primaryLanguage'] = getPrimaryLanguage(movieID, soup = soup)
    data['spokenLanguages'] = getSpokenLanguages(movieID, soup = soup)
    
    # add countries
    data["countries"] = getCountries(movieID, soup = soup)
    
    # add listAppearances
    data['numListAppearances'] = getNumListAppearances(True, movieID, soup = soupLikes)
    
    # add cast
    data['cast'] = getCast(movieID)
    
    # add producers
    data['producers'] = getProducers(movieID, soup = soupCrew)

    # add writers
    data['writers'] = getWriters(movieID, soup = soupCrew)
            
    # add cinematography
    data['cinematography'] = getCinematography(movieID, soup = soupCrew)
    
    # add editors
    data['editors'] = getEditors(movieID, soup = soupCrew)
              
    # add studio(s)
    data['studios'] = []  
    if scriptTag:
        data['studios'] = getStudios(movieID, jsonData = jsonData)
 
    # add link to image of poster
    data['posterLink'] = ""  
    if scriptTag:
        data['posterLink'] = getPosterLink(movieID, jsonData = jsonData)
    
    # add imdbLink
    data['imdbLink'] = getIMDBLink(movieID, soup = soup)
    
    # add backdropLink
    data['backdropLink'] = getBackdropLink(movieID, soup = soup)
    
    # add date Created
    data["dateCreated"] = ""
    if scriptTag:
        data["dateCreated"] = getDateCreated(movieID, jsonData = jsonData)

    # commit changes
    df = pd.DataFrame([data])
    df.to_csv(CSV_FILE_NAME, mode='a', header=not os.path.exists(CSV_FILE_NAME), index=False)
    return True

def populateDatabase(base_url):
    try:
        with open(LAST_PAGE_FILE_NAME, "r") as file:
            page_number = int(file.read().strip())
    except Exception as e:
        page_number = 1
        pass

    while True:
        startPage = time.time()
        url = f"{base_url}/page/{page_number}/"
        response = requestsSession.get(url)
        soup = BeautifulSoup(response.text, 'lxml')
        movie_divs = soup.find_all('div', class_='really-lazy-load')
        if not movie_divs:
            break
        for div in movie_divs:
            startMovie = time.time()
            try:
                addMovieToDatabase(div['data-film-slug'])
            except Exception as e:
                with open(ERROR_FILE_NAME, "a") as file:
                    file.write(f"An error occurred while trying to add movie {div['data-film-slug']}: {e}" + "\n")
            with open(STATS_FILE_NAME, "a") as file:
                file.write(f"{div['data-film-slug']} took {time.time() - startMovie} seconds\n")
        with open(STATS_FILE_NAME, "a") as file:
            file.write(f"\n")
            file.write(f"Page {page_number} took {time.time() - startPage} seconds\n")
            file.write(f"\n")
        print(f"Page {page_number} took {time.time() - startPage} seconds")
        page_number += 1  
        with open(LAST_PAGE_FILE_NAME, "w") as file:
            file.write(str(page_number))

url = f"https://letterboxd.com/sprudelheinz/list/all-the-movies-sorted-by-movie-posters-1"
populateDatabase(url)