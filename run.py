import requests
import subprocess
import pickle
from bs4 import BeautifulSoup

def loadLeaderboardFromFile(filename):
  try:
    with open(filename, "rb") as file:
      leaderboard = pickle.load(file)
  except FileNotFoundError:
    leaderboard = []
  return leaderboard  # loads leaderboard

def usernameInLeaderBoard(username, leaderboard):
  leaderboard_usernames = [tup[1] for tup in leaderboard]
  return username in leaderboard_usernames

LEADERBOARD_FILE = "leaderboard.pickle"

usernames = []

for number in range(1, 10):
  url = f"https://letterboxd.com/members/popular/this/month/page/{number}/"
  response = requests.get(url)
  if response.status_code == 200:
    soup = BeautifulSoup(response.text, 'html.parser')
    table_rows = soup.select('.person-table tbody tr')
    for row in table_rows:
      link = row.find('a', class_='name')
      if link:
        username = link['href'].split('/')[-2]
        usernames.append(username)

for user in usernames:
  leaderboard = loadLeaderboardFromFile(LEADERBOARD_FILE)
  if not usernameInLeaderBoard(user, leaderboard):
    subprocess.run(['python3', 'main.py', user])