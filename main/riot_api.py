import requests
from typing import Final
from dotenv import load_dotenv
import os

RIOT_API: Final[str] = os.getenv('RIOT_API_KEY')
print(RIOT_API)


# Function to check if a summoner exists by summoner name
def check_summoner_exists(summoner_name):
    # Replace 'na1' with the correct region. You can change this to any supported region.
    url = f"https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-name/{summoner_name}"
    headers = {
        "X-Riot-Token": RIOT_API
    }

    response = requests.get(url, headers=headers)

    # If the response is 200, the summoner exists
    if response.status_code == 200:
        return True
    # If the response is 404, the summoner does not exist
    elif response.status_code == 404:
        return False
    else:
        # Other errors (like rate limits, server issues)
        raise Exception(f"Error checking summoner: {response.status_code}")