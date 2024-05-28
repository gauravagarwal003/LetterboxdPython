from bs4 import BeautifulSoup, SoupStrainer
from functions import *
import time
from tqdm import tqdm
import requests
from collections import defaultdict

requestsSession = requests.Session()
username = 'comrade_yui'

start_time = time.time()
if not checkIfUserExists(username):
  print(f'User {username} does not exist')
  exit()
  
result = getDiary(username, date = True)
numDiary = getNumberMoviesInDiary(username)
numPages = ceilDiv(numDiary, filmsPerPageDiary)
baseURL = f"https://letterboxd.com/{username}/films/diary/page"
pageNumber = 1
freq = defaultdict(int)
print(f"It took {time.time() - start_time} seconds to get the diary")
df = pd.read_csv("movies.csv") 
values = df['movieID'].values
while pageNumber <= numPages:
    itTime = time.time()
    response = requestsSession.get(f"{baseURL}/{pageNumber}")
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "lxml", parse_only=SoupStrainer('div', class_="site-body"))
        movies = soup.find_all('tr', class_="diary-entry-row")
        for movie in movies:
            response = requestsSession.get(f"https://letterboxd.com/film/{movie}")
            soup = BeautifulSoup(response.text, 'lxml')
            idTag = movie.find('td', class_="td-actions")
            id = idTag.get('data-film-slug')

            runtime = getRuntime(id, FILE_NAME = "movies.csv", soup = soup)
            if runtime and isMovie(id, dfValues= values, soup = soup):
                tag = movie.find('a', class_="edit-review-button")
                date = tag.get('data-viewing-date')
                freq[date] += runtime
    print(f"Page {pageNumber} took {time.time() - itTime} seconds")
    pageNumber += 1
    
filtered_dict = {key: value for key, value in freq.items() if value <= 1440}
sorted_filtered_dict = dict(sorted(filtered_dict.items(), key=lambda item: item[1], reverse=True))

with open("result.txt", "w") as file:
    file.write('\n')
    
for movie in sorted_filtered_dict:
    with open("result.txt", "a") as file:
        file.write(f'{sorted_filtered_dict[movie]} minutes on {movie}' + "\n")
print(f"It took {time.time() - start_time} seconds total!")