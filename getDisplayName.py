import requests
import pandas as pd
from bs4 import BeautifulSoup, SoupStrainer
import ast


requestsSession = requests.Session()
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
        soup = BeautifulSoup(response.text, 'lxml', parse_only=SoupStrainer("a"))
        title = soup.find(href=lambda href: href and href.startswith(f"/films{iD}"))   
        return title.find('span').get_text()
    

def getDisplayName(iD):
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
        return ""
    
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
    soup = BeautifulSoup(response.text, 'lxml', parse_only=SoupStrainer('head'))
    meta = soup.find('meta', attrs={'name': 'description'})
    if meta:
        description_content = meta.get('content')
        if description_content:
            return description_content[num:]
    return ""
