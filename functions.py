import requests
import pandas as pd
from bs4 import BeautifulSoup, SoupStrainer
import ast

df = pd.read_csv('movies.csv')
requestsSession = requests.Session()


# MISCELLANEOUS FUNCTIONS

#does ceiling division
def ceilDiv(a, b):
  return -(a // -b)

# returns the link for a given genre, director, actor, country, languauge etc.
def getLink(iD): 
    # input: '/actor/ryan-gosling/' or '/language/hindi/'
    #output: 'https://letterboxd.com/actor/ryan-gosling/' or 'https://letterboxd.com/films/language/hindi/' (can return None)
    genres = {'science fiction', 'music', 'thriller', 'horror', 'tv movie', 'action', 'mystery', 'animation', 'romance', 'comedy', 'adventure', 'war', 'history', 'family', 'documentary', 'crime', 'fantasy', 'drama', 'western'}
    link = None
    
    if iD.lower() in genres:
        link = f"https://letterboxd.com/films/genre/{iD.replace(" ", "-")}"
    
    elif iD.startswith("/theme/") or iD.startswith("/nanogenre/") or iD.startswith("/language/") or iD.startswith("/country/"):
        link = f"https://letterboxd.com/films{iD}"
        
    elif iD.startswith("/director/") or iD.startswith("/actor/") or iD.startswith("/producer/") or iD.startswith("/writer/") or iD.startswith("/cinematography/") or iD.startswith("/editor/") or iD.startswith("/studio/"):
        link =  f"https://letterboxd.com{iD}"
    
    if link:
        response = requestsSession.get(link)
        if response.status_code == 200:
            return link
        
    return None    
        
# returns the display name for a given genre, director, actor, country, languauge etc.
def getDisplayName(iD):
    # input: '/actor/ryan-gosling/' or '/language/hindi/'
    # output: 'Ryan Gosling' or 'Hindi' (can return None)
    def has(themes_list, target_string):
        return any(target_string.lower() in theme.lower() for theme in themes_list)

    def getDisplayNameThemeNanoGenre(name, columnLabel, iD):
        df = pd.read_csv('movies.csv')
        df[columnLabel] = df[columnLabel].apply(ast.literal_eval)
        movieID = None
        for index, row in df.iterrows():
            if has(row[columnLabel], iD):
                movieID = row['movieID']
        if movieID:
            response = requestsSession.get(f"https://letterboxd.com/film/{movieID}/{name}s/")
            if response.status_code != 200:
                return None
            soup = BeautifulSoup(response.text, 'lxml', parse_only=SoupStrainer("a"))
            title = soup.find(href=lambda href: href and href.startswith(f"/films{iD}"))   
            return title.find('span').get_text()
    

    if not isinstance(iD, str):
        return iD
    
    if iD.startswith("/theme/"):
        return getDisplayNameThemeNanoGenre('theme', 'themes', iD)
    
    if iD.startswith("/nanogenre/"):
        return getDisplayNameThemeNanoGenre('nanogenre', 'nanoGenres', iD)
    
    if iD.startswith("/language/"):
        response = requestsSession.get(f"https://letterboxd.com/countries/")
        soup = BeautifulSoup(response.text, 'lxml')
        with open("result.txt", "w") as f:
            f.write(soup.prettify())
        aTag = soup.find('a', attrs={'href': f'/films{iD}'})
        if aTag:
            span = aTag.find('span')
            if span:
                return span.text
        return None
    
    elif iD.startswith("/country/"):
        response = requestsSession.get(f"https://letterboxd.com/countries/")
        soup = BeautifulSoup(response.text, 'lxml')
        with open("result.txt", "w") as f:
            f.write(soup.prettify())
        aTag = soup.find('a', attrs={'href': f'/films{iD}'})
        if aTag:
            span = aTag.find('span')
            if span:
                return span.text
        return ""  
    
    elif iD.startswith("/director/"):
        num = 17
    elif iD.startswith("/actor/"):
        num = 15
    elif iD.startswith("/producer/"):
        num = 18
    elif iD.startswith("/writer/"):
        num = 17
    elif iD.startswith("/cinematography/"):
        num = 14
    elif iD.startswith("/editor/"):
        num = 16
    elif iD.startswith("/studio/"):
        num = 18
    else:
        return ""
    
    response = requestsSession.get(f"https://letterboxd.com/{iD}/")
    if response.status_code != 200:
        return None
    soup = BeautifulSoup(response.text, 'lxml', parse_only=SoupStrainer('head'))
    meta = soup.find('meta', attrs={'name': 'description'})
    if meta:
        description_content = meta.get('content')
        if description_content:
            return description_content[num:]
    return ""
    
# checks if a movie is in the database
def isMovieInDatabase(movieID):
    # returns True or False
    try:
        if df.empty:
            return False
        else:
            return movieID in df['movieID'].values
    except pd.errors.EmptyDataError:
        return False

# returns the number of movies watched by a user
def getNumberMoviesWatched(username):
    # can return None
    response = requestsSession.get(f"https://letterboxd.com/{username}/")
    if response.status_code != 200:
        return None
    soup = BeautifulSoup(response.text, "lxml")
    first_h4 = soup.find('h4', class_='profile-statistic')
    if first_h4:
        span_value = first_h4.find('span', class_='value')
        if span_value:
            text_inside_span = span_value.get_text()
            numMovies = int(''.join(c for c in text_inside_span if c.isdigit()))
            if numMovies:
                return numMovies

# checks if movie is on Letterboxd
def isValidMovie(filmID):
    # returns True or False
    response = requestsSession.get(f"https://letterboxd.com/film/{filmID}")
    if response.status_code == 200:
        return True
    else:
        return False

# checks if the given ID is a movie using the TMDB link 
# soup can be any tab from the movie page except nanogenres, themes, and similar
def isMovie(iD, soup = None):
    # returns True or False
    if iD in df['movieID'].values:
        return True
    if not isValidMovie(iD):
        return False
    if not soup:
        response = requestsSession.get(f"https://letterboxd.com{iD}")
        soup = BeautifulSoup(response.text, 'lxml')
    tmdbLink = soup.find_all('a', attrs={'data-track-action': 'TMDb'})
    for link in tmdbLink:
        href = link.get('href')
        if href and "/movie/" in href:
            return True
            
    return False

    
# GET DETAILS THAT DON"T CHANGE
#------------------------------------------------------------


# gets the title of a movie
# soup can be any tab from the movie page except nanogenres, themes, and similar 
def getTitle(filmID, soup = None):
    # input: 'barbie'
    # output: 'Barbie' (can return None)
    if filmID in df['movieID'].values:
        return df.loc[df['movieID'] == filmID, 'title'].values[0]

    if not soup:
        response = requestsSession.get(f"https://letterboxd.com/film/{filmID}")
        soup = BeautifulSoup(response.text, 'lxml')
        
    try:
        title = soup.find('span', class_ = "name js-widont prettify").get_text()
        return title
    except Exception as e:
        return None

# gets the release year of a movie
# soup can be any tab from the movie page except nanogenres, themes, and similar 
def getReleaseYear(filmID, soup = None):
    # input: 'barbie'
    # output: 2023 (can return None)
    if not isValidMovie(filmID):
        return None
    if filmID in df['movieID'].values:
        return df.loc[df['movieID'] == filmID, 'year'].values[0]
    
    if not soup:
        response = requestsSession.get(f"https://letterboxd.com/film/{filmID}")
        soup = BeautifulSoup(response.text, 'lxml')
    try:
        releaseYearDiv = soup.find("div", class_="releaseyear")
        if releaseYearDiv:
            aTag = releaseYearDiv.find("a")
            if aTag:
                return  int(aTag.text.strip())
    except Exception as e:
        return None
    
    
# GET DETAILS THAT CHANGE
# current is False if you want to get info from database and True if you want the current info
#------------------------------------------------------------

# checks if the movie has more views than the given number
# soup is can be likes, reviews, or lists tab
def getnumViews(current, movieID, soup = None):
    if not current:
        if movieID in df['movieID'].values:
            return df.loc[df['movieID'] == movieID, 'numViews'].values[0]        
        
    if not soup:
        response = requestsSession.get(f"https://letterboxd.com/film/{movieID}/likes")
        soup = BeautifulSoup(response.text, 'lxml')
        
    aTag = soup.find("a", href=f"/film/{movieID}/members/")
    print(aTag)
    if aTag and aTag.has_attr("title"):
        return int(''.join(filter(str.isdigit, aTag["title"])))    
    return None
 
# gets the average rating for a film
def getAverageRating(filmID):
    # input: 'barbie'
    # output: 3.87 (can return None)
    if filmID in df['movieID'].values:
        return df.loc[df['movieID'] == filmID, 'avgRating'].values[0]
    response = requestsSession.get(f"https://letterboxd.com/csi/film/{filmID}/rating-histogram/")
    if response.status_code != 200:
        return None
    soup = BeautifulSoup(response.text, 'lxml')

    try: # try extracting the average ratings and total ratings
        ratingsText = soup.find('a', {'class': 'tooltip', 'title': True}).get('title')
        return float(ratingsText.split()[3])
    except Exception as e:
        return None
 
    
print(getAverageRating('lips-2005'))