import pandas as pd
import os

# --- Load all three datasets ---
print("Loading raw data...")
results = pd.read_csv("data/raw/results_all.csv")
qualifying = pd.read_csv("data/raw/qualifying_all.csv")
calendar = pd.read_csv("data/raw/race_calendar.csv")

print(f"Results: {len(results)} rows")
print(f"Qualifying: {len(qualifying)} rows")
print(f"Calendar: {len(calendar)} rows")

# --- Tag circuit types ---
# This is what lets the chatbot answer "street circuit" questions
STREET_CIRCUITS = [
    "Monaco Grand Prix Circuit",
    "Baku City Circuit", 
    "Marina Bay Street Circuit",
    "Circuit de Monaco",
    "Valencia Street Circuit",
    "Adelaide Street Circuit",
    "Miami International Autodrome",
    "Las Vegas Strip Street Circuit",
    "Jeddah Corniche Circuit",
]

HIGH_SPEED_CIRCUITS = [
    "Autodromo Nazionale di Monza",
    "Circuit de Spa-Francorchamps",
    "Silverstone Circuit",
    "Circuit Gilles Villeneuve",
    "Bahrain International Circuit",
    "Suzuka Circuit",
]

def tag_circuit_type(circuit_name):
    if any(s.lower() in circuit_name.lower() for s in STREET_CIRCUITS):
        return "street"
    elif any(h.lower() in circuit_name.lower() for h in HIGH_SPEED_CIRCUITS):
        return "high_speed"
    else:
        return "mixed"

calendar['circuit_type'] = calendar['circuit'].apply(tag_circuit_type)

print(f"\nCircuit types:")
print(calendar['circuit_type'].value_counts())

# --- Merge results with calendar (adds weather + circuit_type) ---
print("\nMerging datasets...")
merged = results.merge(
    calendar[['year', 'round', 'weather', 'circuit_type', 'date']],
    on=['year', 'round'],
    how='left'
)

# --- Merge with qualifying (adds quali position) ---
quali_slim = qualifying[['year', 'round', 'driver_full', 'quali_position', 'q1', 'q2', 'q3']]
merged = merged.merge(
    quali_slim,
    on=['year', 'round', 'driver_full'],
    how='left'
)

# --- Clean up ---
merged['position'] = pd.to_numeric(merged['position'], errors='coerce')
merged['grid'] = pd.to_numeric(merged['grid'], errors='coerce')
merged['quali_position'] = pd.to_numeric(merged['quali_position'], errors='coerce')
merged['points'] = pd.to_numeric(merged['points'], errors='coerce')

# Add positions gained/lost column (race craft indicator)
merged['positions_gained'] = merged['grid'] - merged['position']

print(f"Master dataset: {len(merged)} rows")
print(f"Columns: {list(merged.columns)}")

# --- Save ---
os.makedirs("data/processed", exist_ok=True)
merged.to_csv("data/processed/master.csv", index=False)
print("\nSaved to data/processed/master.csv")

# --- Quick sanity check ---
print("\n--- Sample: Verstappen wet races ---")
ver_wet = merged[
    (merged['driver_full'] == 'Max Verstappen') & 
    (merged['weather'] == 'wet')
][['year', 'race_name', 'grid', 'position', 'positions_gained', 'weather']]
print(ver_wet)