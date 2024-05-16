import pandas as pd
import os
import requests
import json
from bs4 import BeautifulSoup, SoupStrainer
import time
from functions import *

minViews = 25000
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
    if isMovieInDatabase(movieID):
        return False
    
    response = requestsSession.get(f"https://letterboxd.com/film/{movieID}/details")
    responseLikes = requestsSession.get(f"https://letterboxd.com/film/{movieID}/likes")
        
    soup = BeautifulSoup(response.text, 'lxml')
    soupLikes = BeautifulSoup(responseLikes.text, 'lxml')

    # check if movie satisfies minimum views
    if getnumViews(True, movieID, soupLikes) < minViews:
        return False
        
    # check if movie is a TV show or miniseries (according to TMDB link)
    if not isMovie(movieID, soup):
        return False
    
    responseHistogram = requestsSession.get(f"https://letterboxd.com/csi/film/{movieID}/rating-histogram/")
    responseThemes = requestsSession.get(f"https://letterboxd.com/film/{movieID}/themes")
    responseNanoGenres = requestsSession.get(f"https://letterboxd.com/film/{movieID}/nanogenres")
    responseCrew = requestsSession.get(f"https://letterboxd.com/film/{movieID}/crew")


    histogram = BeautifulSoup(responseHistogram.text, "lxml", parse_only=  SoupStrainer("li", class_="rating-histogram-bar"))
    soupThemes = BeautifulSoup(responseThemes.text, 'lxml')
    soupNanoGenres = BeautifulSoup(responseNanoGenres.text, 'lxml')
    soupCrew = BeautifulSoup(responseCrew.text, 'lxml')

    data = {}
    
    # add movie id
    data['movieID'] = movieID 
    
    # add title
    data['title'] = getnumViews(True, movieID, soupLikes)
    
    # add average rating
    data['avgRating'] = getAverageRating(movieID)
    
    # add year
    data['year'] = getReleaseYear(movieID, soup)

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
        if "aggregateRating" in jsonData:
            if "ratingCount" in jsonData['aggregateRating']:
                data['numTotalRatings'] = jsonData['aggregateRating']['ratingCount']

            if "reviewCount" in jsonData['aggregateRating']:
                data['numReviews'] = jsonData['aggregateRating']['reviewCount']            

    tooltip_elements = histogram.find_all('a', class_ = 'ir tooltip')
    # add histogram data 
    for element in tooltip_elements: 
        num = int(''.join(c for c in element.text.split()[0] if c.isdigit()))
        stars = starsToInt[element.text.split()[1]]
        data[f"num{stars}StarRatings"] = num

    # set any missing histogram data to 0
    for i in starsToInt.values(): 
        if f"num{i}StarRatings" not in data:
            data[f"num{i}StarRatings"] = 0
    
    # add director(s)
    data['director'] = []    
    if scriptTag:
        if "director" in jsonData:
            for director in jsonData['director']:
                data['director'].append(director['sameAs'])
    
    # add views
    data['numViews'] = 0
    aTag = soupLikes.find("a", href=f"/film/{movieID}/members/")
    if aTag and aTag.has_attr("title"):
        data['numViews'] = int(''.join(filter(str.isdigit, aTag["title"])))
    
    # add likes
    data['numLikes'] = 0
    aTag = soupLikes.find("a", href=f"/film/{movieID}/members/")
    if aTag and aTag.has_attr("title"):
        data['numLikes'] = int(''.join(filter(str.isdigit, aTag["title"])))
        
    # add fans
    data['numFans'] = 0
    aTag = soupLikes.find("a", href=f"/film/{movieID}/fans/")
    if aTag and aTag.has_attr("title"):
        data['numFans'] = int(''.join(filter(str.isdigit, aTag["title"])))
    
    #add genre(s)
    data['genres'] = []
    if scriptTag:
        if "genre" in jsonData:
            for genre in jsonData['genre']:
                data['genres'].append(genre)
                
    # add themes
    data['themes'] = []
    aTags = soupThemes.find_all("a", href=lambda href: href and href.startswith("/films/theme/"))
    if aTags:
        for aTag in aTags:
            rawTheme = aTag.get("href")
            theme = rawTheme[6:-14]
            data['themes'].append(theme)
                    
    # add nanogenres
    data['nanoGenres'] = []
    aTags = soupNanoGenres.find_all("a", href=lambda href: href and href.startswith("/films/nanogenre/"))
    if aTags:
        for aTag in aTags:
            rawNanoGenre = aTag.get("href")
            nanoGenre = rawNanoGenre[6:-14]
            data['nanoGenres'].append(nanoGenre)
    
    # add runtime
    data['runtime'] = 0
    pTag = soup.find('p', class_='text-link text-footer')

    if pTag:
        try:
            runtimeRaw = pTag.get_text()
            data['runtime'] = int(runtimeRaw.split()[0])
        except:
            return False
    else:
        return False
        
    # add primary and secondary languages
    data['primaryLanguage'] = ""
    data['spokenLanguages'] = []
    aTags = soup.find_all("a", href=lambda href: href and href.startswith("/films/language/"))
    if aTags:
        data['primaryLanguage'] = aTags[0].get("href")[6:]
        for aTag in aTags[1:]:
            language = aTag.get("href")[6:]
            data['spokenLanguages'].append(language)
    
    # add countries
    data["countries"] = []
    aTags = soup.find_all("a", href=lambda href: href and href.startswith("/films/country/"))
    if aTags:
        for aTag in aTags:
            country = aTag['href'][6:]
            data["countries"].append(country)
    
    # add listAppearances
    data['numListAppearances'] = 0
    aTag = soupLikes.find("a", href=f"/film/{movieID}/lists/")
    if aTag and aTag.has_attr("title"):
        data['numListAppearances'] = int(''.join(filter(str.isdigit, aTag["title"])))
    
    # add cast
    notAllowed = ['(uncredited)', '(archive footage)', '(voice / uncredited)', '(voice/uncredited)', '(unconfirmed)', '(uncredited voice)', '(voice, uncredited)']
    responseCast = requestsSession.get(f"https://letterboxd.com/film/{movieID}/")
    soup = BeautifulSoup(responseCast.text, 'lxml')
    data['cast'] = []
    castList = soup.find('div', class_ = 'cast-list')
    if castList:
        actors = castList.find_all('a', class_ = 'text-slug tooltip')
        for actor in actors:
            if actor.get('title'):
                add = True
                for rule in notAllowed:
                    if rule in actor.get('title'):
                        add = False
                if add:
                    data['cast'].append(actor.get('href'))
    
    # add producers
    data['producers'] = []
    aTags = soupCrew.find_all("a", href=lambda href: href and href.startswith("/producer/"))
    if aTags:
        for aTag in aTags:
            producer = aTag.get("href")
            data['producers'].append(producer)

    # add writers
    data['writers'] = []
    aTags = soupCrew.find_all("a", href=lambda href: href and href.startswith("/writer/"))
    if aTags:
        for aTag in aTags:
            writer = aTag.get("href")
            data['writers'].append(writer)
            
    # add cinematography
    data['cinematography'] = []
    aTags = soupCrew.find_all("a", href=lambda href: href and href.startswith("/cinematography/"))
    if aTags:
        for aTag in aTags:
            cin = aTag.get("href")
            data['cinematography'].append(cin)
    
    # add editors
    data['editors'] = []
    aTags = soupCrew.find_all("a", href=lambda href: href and href.startswith("/editor/"))
    if aTags:
        for aTag in aTags:
            editor = aTag.get("href")
            data['editors'].append(editor)  
              
    # add studio(s)
    data['studios'] = []  
    if scriptTag:
        if "productionCompany" in jsonData:
            for studio in jsonData['productionCompany']:
                data['studios'].append(studio['sameAs'])
 
    # add link to image of poster
    data['posterLink'] = ""  
    if scriptTag:
        if "image" in jsonData:
            data['posterLink'] = jsonData['image']  
    
    # add imdbLink
    data['imdbLink'] = ""
    IMDbTag = soup.find('a', {'data-track-action': 'IMDb'})
    if IMDbTag:
        data['imdbLink'] = IMDbTag['href']          
    
    # add backdropLink
    data['backdropLink'] = ""
    metaTag = soup.find('meta', attrs={'name': 'twitter:image'})
    if metaTag:
        backdropURL = metaTag.get('content')
        if backdropURL != data['posterLink']: # makes sure backdrop is not the same as poster
            data['backdropLink'] = backdropURL

    # add date Created
    data["dateCreated"] = ""
    if scriptTag:
        if "dateCreated" in jsonData:
            data["dateCreated"] = jsonData["dateCreated"]    

    # commit changes
    df = pd.DataFrame([data])
    df.to_csv('movies.csv', mode='a', header=not os.path.exists('movies.csv'), index=False)
    return True

base_url = f"https://letterboxd.com/sprudelheinz/list/all-the-movies-sorted-by-movie-posters-1/"
try:
    with open("last_page.txt", "r") as file:
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
            with open("error.txt", "a") as file:
                file.write(f"An error occurred while trying to add movie {div['data-film-slug']}: {e}")
        with open("stats.txt", "a") as file:
            file.write(f"{div['data-film-slug']} took {time.time() - startMovie} seconds\n")
    with open("stats.txt", "a") as file:
        file.write(f"\n")
        file.write(f"Page {page_number} took {time.time() - startPage} seconds\n")
        file.write(f"\n")
    print(f"Page {page_number} took {time.time() - startPage} seconds")
    page_number += 1  
    with open("last_page.txt", "w") as file:
        file.write(str(page_number))