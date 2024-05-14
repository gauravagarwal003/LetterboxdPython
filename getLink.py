genres = {'science fiction', 'music', 'thriller', 'horror', 'tv movie', 'action', 'mystery', 'animation', 'romance', 'comedy', 'adventure', 'war', 'history', 'family', 'documentary', 'crime', 'fantasy', 'drama', 'western'}

def getLink(iD):    
    if iD.lower() in genres:
        return f"https://letterboxd.com/films/genre/{iD.replace(" ", "-")}"
    
    elif iD.startswith("/theme/") or iD.startswith("/nanogenre/") or iD.startswith("/language/") or iD.startswith("/country/"):
        return f"https://letterboxd.com/films{iD}"
        
    elif iD.startswith("/director/") or iD.startswith("/actor/") or iD.startswith("/producer/") or iD.startswith("/writer/") or iD.startswith("/cinematography/") or iD.startswith("/editor/") or iD.startswith("/studio/"):
        return f"https://letterboxd.com{iD}"