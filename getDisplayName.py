import requests
from bs4 import BeautifulSoup, SoupStrainer

requestsSession = requests.Session()

def getDisplayName(iD):
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
