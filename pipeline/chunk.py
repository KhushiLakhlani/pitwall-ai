import pandas as pd
import json
import os

# Load master dataset
print("Loading master dataset...")
df = pd.read_csv("data/processed/master.csv")
print(f"Loaded {len(df)} rows")

chunks = []

# --- Chunk Type 1: Individual Race Performance ---
print("\nCreating race performance chunks...")
for _, row in df.iterrows():
    text = f"{row['driver_full']} finished position {row['position']} at {row['race_name']} {row['year']}. "
    text += f"Started from grid position {row['grid']}. "
    text += f"Positions gained/lost: {row['positions_gained']}. "
    text += f"Circuit: {row['circuit']} ({row['circuit_type']} circuit). "
    text += f"Weather: {row['weather']}. "
    text += f"Team: {row['constructor']}. "
    text += f"Points scored: {row['points']}. "
    text += f"Race status: {row['status']}."

    chunks.append({
        "chunk_id": f"race_{row['year']}_{row['round']}_{row['driver_full'].replace(' ', '_')}",
        "text": text,
        "metadata": {
            "type": "race_result",
            "driver": row['driver_full'],
            "year": int(row['year']),
            "race": row['race_name'],
            "circuit": row['circuit'],
            "circuit_type": str(row['circuit_type']),
            "weather": str(row['weather']),
            "position": str(row['position']),
            "constructor": row['constructor'],
        }
    })

print(f"  → {len(chunks)} race chunks created")

# --- Chunk Type 2: Driver Season Summary ---
print("\nCreating season summary chunks...")
season_chunks = []
for (driver, year), group in df.groupby(['driver_full', 'year']):
    total_races = len(group)
    wins = len(group[group['position'] == 1])
    podiums = len(group[group['position'] <= 3])
    total_points = group['points'].sum()
    avg_position = group['position'].mean().round(2)
    avg_grid = group['grid'].mean().round(2)
    wet_races = group[group['weather'] == 'wet']
    avg_wet_position = wet_races['position'].mean().round(2) if len(wet_races) > 0 else "no wet races"
    street_races = group[group['circuit_type'] == 'street']
    avg_street_position = street_races['position'].mean().round(2) if len(street_races) > 0 else "no street circuits"

    text = f"{driver} in the {year} F1 season: "
    text += f"Competed in {total_races} races. "
    text += f"Won {wins} races, achieved {podiums} podiums. "
    text += f"Total points: {total_points}. "
    text += f"Average finish position: {avg_position}. "
    text += f"Average qualifying position: {avg_grid}. "
    text += f"Average finish in wet conditions: {avg_wet_position}. "
    text += f"Average finish at street circuits: {avg_street_position}. "
    text += f"Team: {group['constructor'].iloc[0]}."

    season_chunks.append({
        "chunk_id": f"season_{year}_{driver.replace(' ', '_')}",
        "text": text,
        "metadata": {
            "type": "season_summary",
            "driver": driver,
            "year": int(year),
            "constructor": group['constructor'].iloc[0],
            "wins": int(wins),
            "podiums": int(podiums),
        }
    })

chunks.extend(season_chunks)
print(f"  → {len(season_chunks)} season summary chunks created")

# --- Chunk Type 3: Driver Career Summary ---
print("\nCreating career performance chunks...")
career_chunks = []
for driver, group in df.groupby('driver_full'):
    wet_races = group[group['weather'] == 'wet']
    street_races = group[group['circuit_type'] == 'street']
    total_races = len(group)
    wins = len(group[group['position'] == 1])

    text = f"{driver} career F1 summary ({group['year'].min()}-{group['year'].max()}): "
    text += f"Total races: {total_races}. Total wins: {wins}. "

    if len(wet_races) > 0:
        text += f"Wet race record: {len(wet_races)} wet races, "
        text += f"average finish position {wet_races['position'].mean().round(2)}, "
        text += f"wins in wet: {len(wet_races[wet_races['position'] == 1])}. "
    else:
        text += "No wet race data available. "

    if len(street_races) > 0:
        text += f"Street circuit record: {len(street_races)} races, "
        text += f"average finish position {street_races['position'].mean().round(2)}, "
        text += f"wins at street circuits: {len(street_races[street_races['position'] == 1])}. "
    else:
        text += "No street circuit data available. "

    career_chunks.append({
        "chunk_id": f"career_{driver.replace(' ', '_')}",
        "text": text,
        "metadata": {
            "type": "career_summary",
            "driver": driver,
            "total_races": int(total_races),
            "total_wins": int(wins),
        }
    })

chunks.extend(career_chunks)
print(f"  → {len(career_chunks)} career summary chunks created")

# --- Save all chunks ---
os.makedirs("data/chunks", exist_ok=True)
with open("data/chunks/all_chunks.json", "w") as f:
    json.dump(chunks, f, indent=2)

print(f"\n Total chunks created: {len(chunks)}")
print(f"Saved to data/chunks/all_chunks.json")

# --- Preview ---
print("\n--- Sample career chunk for Verstappen ---")
ver_chunk = [c for c in chunks if c['chunk_id'] == 'career_Max_Verstappen']
if ver_chunk:
    print(ver_chunk[0]['text'])