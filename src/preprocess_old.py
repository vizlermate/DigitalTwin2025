"""
build_trips.py — Precompute bike trips paths on Manhattan street graph and save to a file
Usage:
    python build_trips.py
Output:
    trips.pkl — pickled list of precomputed trips
"""

import pandas as pd
import networkx as nx
from math import hypot
import pickle

# ---------- SETTINGS ----------
GRAPHML_FILE = "data\\manhatten.graphml"
CSV_FILE = "data\\202401-part1.csv"
MAX_TRIPS = 200000
NODE_EPS = 1e-9

# ---------- LOAD GRAPH ----------
print("Loading graph...")
graph = nx.read_graphml(GRAPHML_FILE)

# Ensure edge "length" is numeric (fallback to euclidean)
for u, v, data in graph.edges(data=True):
    if "length" in data:
        try:
            data["length"] = float(data["length"])
        except Exception:
            data["length"] = 1.0
    else:
        x1, y1 = float(graph.nodes[u]['x']), float(graph.nodes[u]['y'])
        x2, y2 = float(graph.nodes[v]['x']), float(graph.nodes[v]['y'])
        data["length"] = ((x1 - x2)**2 + (y1 - y2)**2) ** 0.5

# Node coordinate ranges
xs = [float(graph.nodes[n]['x']) for n in graph.nodes]
ys = [float(graph.nodes[n]['y']) for n in graph.nodes]
MIN_LON, MAX_LON = min(xs), max(xs)
MIN_LAT, MAX_LAT = min(ys), max(ys)

def latlon_to_xy(lat, lon):
    WIDTH, HEIGHT = 600, 600
    x = (lon - MIN_LON) / (MAX_LON - MIN_LON) * WIDTH
    y = HEIGHT - (lat - MIN_LAT) / (MAX_LAT - MIN_LAT) * HEIGHT
    return x, y

# Precompute node positions
positions = {
    n: latlon_to_xy(float(data['y']), float(data['x']))
    for n, data in graph.nodes(data=True)
}

# ---------- HELPER: NEAREST NODE ----------
def nearest_node(lat, lon):
    best_node = None
    best_dist = float("inf")
    for n, data in graph.nodes(data=True):
        dx = lon - float(data['x'])
        dy = lat - float(data['y'])
        dist = dx*dx + dy*dy
        if dist < best_dist:
            best_dist = dist
            best_node = n
    return best_node

# ---------- LOAD BIKE TRIPS ----------
print("Loading bike trips CSV...")
df = pd.read_csv(CSV_FILE, low_memory=False, parse_dates=["started_at", "ended_at"])
df = df.dropna(subset=['start_lat', 'start_lng', 'end_lat', 'end_lng'])
df_sorted = df.sort_values("started_at").reset_index(drop=True)

# ---------- BUILD TRIPS ----------
# ---------- BUILD TRIPS ----------
trips = []
done = 0

for _, row in df_sorted.iterrows():
    # Only keep trips starting in 2024
    if row["started_at"].year != 2024:
        continue

    start_node = nearest_node(row['start_lat'], row['start_lng'])
    end_node   = nearest_node(row['end_lat'], row['end_lng'])

    try:
        path_nodes = nx.shortest_path(graph, start_node, end_node, weight="length")
    except nx.NetworkXNoPath:
        continue

    path_coords = [positions[n] for n in path_nodes]
    if len(path_coords) < 2:
        continue

    segments = []
    total_len = 0.0
    for i in range(len(path_coords) - 1):
        x1, y1 = path_coords[i]
        x2, y2 = path_coords[i+1]
        seg_len = hypot(x2 - x1, y2 - y1)
        if seg_len <= NODE_EPS:
            continue
        segments.append((i, seg_len))
        total_len += seg_len

    if total_len <= 0:
        continue

    duration = (row["ended_at"] - row["started_at"]).total_seconds()
    if duration <= 0:
        continue

    trips.append({
        "path": path_coords,
        "segments": segments,
        "total_length": total_len,
        "type": row['rideable_type'],
        "start_time": row["started_at"],
        "end_time": row["ended_at"],
        "duration": duration,
        "finished": False
    })

    if len(trips) % 1000 == 0:
        done += 1000
        print(done)

    if len(trips) >= MAX_TRIPS:
        break


# ---------- SAVE TRIPS ----------
with open("data\\trips_200k.pkl", "wb") as f:
    pickle.dump(trips, f)

print(f"Saved {len(trips)} trips to trips.pkl")
