from bs4 import BeautifulSoup, SoupStrainer
from functions import getDiary, checkIfUserExists, getTitle
import time
import requests

requestsSession = requests.Session()
username = 'elisabetnorgard'

start_time = time.time()
if not checkIfUserExists(username):
  print(f'User {username} does not exist')
  exit()
  
result = getDiary(username)

if len(result) == 0:
  print(f'User {username} has not watched anything. Go watch something!')
  exit()
print(f"It took {time.time() - start_time} seconds to get the diary")
start_time = time.time()
freq = {}
for entry in result:
  if entry['movieID'] in freq:
    freq[entry['movieID']] += 1
  else:
    freq[entry['movieID']] = 1
print(f"It took {time.time() - start_time} seconds to parse the diary")
start_time = time.time()

filtered_dict = {key: value for key, value in freq.items() if value > 1}

if len(filtered_dict) == 0:
  print(f'User {username} has not rewatched anything. Go rewatch something!')
  exit()

sorted_filtered_dict = dict(
    sorted(filtered_dict.items(), key=lambda item: item[1], reverse=True))

for movie in sorted_filtered_dict:
  print(f'{sorted_filtered_dict[movie]} times: {getTitle(movie, FILE_NAME = "movies.csv")}')
print(f"It took {time.time() - start_time} seconds to filter and sort the movies")
