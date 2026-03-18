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

def get_race_results(year):
    results = []
    offset = 0
    limit = 100

    while True:
        url = f"https://api.jolpi.ca/ergast/f1/{year}/results/?limit={limit}&offset={offset}&format=json"
        data = fetch_with_retry(url)

        if data is None:
            print(f"  Failed to fetch {year} offset {offset}, skipping...")
            break

        races = data['MRData']['RaceTable']['Races']
        total = int(data['MRData']['total'])

        for race in races:
            for result in race['Results']:
                results.append({
                    'year': year,
                    'round': race['round'],
                    'race_name': race['raceName'],
                    'circuit': race['Circuit']['circuitName'],
                    'country': race['Circuit']['Location']['country'],
                    'driver': result['Driver']['familyName'],
                    'driver_full': f"{result['Driver']['givenName']} {result['Driver']['familyName']}",
                    'constructor': result['Constructor']['name'],
                    'grid': result['grid'],
                    'position': result['position'],
                    'status': result['status'],
                    'points': result['points'],
                })

        offset += limit
        if offset >= total:
            break

        time.sleep(1.5)

    return pd.DataFrame(results)

# --- Main ---
print("Starting race results pull...")
all_data = []
years = range(2000, 2026)

for year in years:
    print(f"Fetching {year}...")
    df = get_race_results(year)
    print(f"  → {len(df)} rows")
    all_data.append(df)
    time.sleep(2)

full_df = pd.concat(all_data, ignore_index=True)
print(f"\nTotal rows: {len(full_df)}")
print(f"Years covered: {full_df['year'].min()} → {full_df['year'].max()}")
print(f"Unique drivers: {full_df['driver_full'].nunique()}")
print(f"Unique circuits: {full_df['circuit'].nunique()}")

os.makedirs("data/raw", exist_ok=True)
full_df.to_csv("data/raw/results_all.csv", index=False)
print("\nSaved to data/raw/results_all.csv")