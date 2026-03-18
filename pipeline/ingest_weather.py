import requests
import pandas as pd
import os
import time

def fetch_with_retry(url, max_retries=5):
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=15)
            if response.status_code == 200 and response.text.strip():
                return response.json()
            else:
                print(f"  Empty response, waiting {2 ** attempt}s...")
                time.sleep(2 ** attempt)
        except Exception as e:
            print(f"  Error: {e}, waiting {2 ** attempt}s...")
            time.sleep(2 ** attempt)
    return None

def get_races_for_year(year):
    """Get all race names and rounds for a year"""
    url = f"https://api.jolpi.ca/ergast/f1/{year}/?format=json"
    data = fetch_with_retry(url)
    if not data:
        return []
    
    races = data['MRData']['RaceTable']['Races']
    return [{'year': year, 'round': r['round'], 'race_name': r['raceName'],
             'circuit': r['Circuit']['circuitName'],
             'country': r['Circuit']['Location']['country'],
             'date': r['date']} for r in races]

# Known wet/mixed races - manually curated list
# This is more reliable than scraping weather APIs for historical data
WET_RACES = {
    # Format: "year_round": "wet" or "mixed"
    "2000_2": "wet",    # Brazilian GP
    "2003_16": "wet",   # Japanese GP
    "2007_15": "wet",   # Japanese GP (Fuji)
    "2008_16": "wet",   # Japanese GP (Fuji)
    "2008_17": "wet",   # Chinese GP
    "2009_1": "wet",    # Malaysian GP
    "2010_7": "wet",    # Malaysian GP
    "2011_5": "mixed",  # Turkish GP
    "2011_8": "wet",    # Canadian GP
    "2012_5": "wet",    # Malaysian GP
    "2013_6": "wet",    # Canadian GP
    "2014_3": "mixed",  # Bahrain GP
    "2015_5": "wet",    # Spanish GP
    "2016_1": "wet",    # Australian GP
    "2016_3": "wet",    # Chinese GP
    "2017_9": "wet",    # Canadian GP
    "2019_12": "wet",   # German GP
    "2021_10": "wet",   # Belgian GP
    "2021_18": "wet",   # Russian GP
    "2022_2": "wet",    # Saudi Arabian GP
    "2023_6": "wet",    # Monaco GP
}

print("Building race calendar with weather tags...")
all_races = []
years = range(2000, 2026)

for year in years:
    print(f"Fetching calendar {year}...")
    races = get_races_for_year(year)
    for race in races:
        key = f"{race['year']}_{race['round']}"
        race['weather'] = WET_RACES.get(key, 'dry')
    all_races.extend(races)
    time.sleep(1)

df = pd.DataFrame(all_races)
print(f"\nTotal races: {len(df)}")
print(f"Wet races: {len(df[df['weather'] == 'wet'])}")
print(f"Mixed races: {len(df[df['weather'] == 'mixed'])}")
print(f"Dry races: {len(df[df['weather'] == 'dry'])}")

os.makedirs("data/raw", exist_ok=True)
df.to_csv("data/raw/race_calendar.csv", index=False)
print("\nSaved to data/raw/race_calendar.csv")