import pygame
import csv
from datetime import datetime, timedelta
import networkx as nx
import osmnx as ox
import numpy as np
np.float_ = np.float64

# ---------------- CONFIG -----------------
BIKE_DATA_FILE = "Assets\\Data\\historical_data.csv"
MANHATTAN_GRAPH_FILE = "Assets\\Data\\manhattan.graphml"
NUMBER_OF_TRIPS = 5000
SCREEN_WIDTH = 700
SCREEN_HEIGHT = 700
FPS = 60
SIMULATION_SPEED = 1.0

# ---------------- HELPERS -----------------
def is_ongoing(current_time, start_time, end_time):
    return start_time <= current_time <= end_time


def coordinates_to_pixel(lat, lng, min_lat, max_lat, min_lng, max_lng, zoom=1.0, offset_x=0, offset_y=0):
    x = (lng - min_lng) / (max_lng - min_lng) * SCREEN_WIDTH
    y = SCREEN_HEIGHT - (lat - min_lat) / (max_lat - min_lat) * SCREEN_HEIGHT
    # Apply zoom and pan
    x = (x - SCREEN_WIDTH / 2) * zoom + SCREEN_WIDTH / 2 + offset_x
    y = (y - SCREEN_HEIGHT / 2) * zoom + SCREEN_HEIGHT / 2 + offset_y
    return int(x), int(y)


def draw_graph(screen, G, min_lat, max_lat, min_lng, max_lng, zoom, offset_x, offset_y):
    for u, v, data in G.edges(data=True):
        lat1, lng1 = float(G.nodes[u]["y"]), float(G.nodes[u]["x"])
        lat2, lng2 = float(G.nodes[v]["y"]), float(G.nodes[v]["x"])
        x1, y1 = coordinates_to_pixel(lat1, lng1, min_lat, max_lat, min_lng, max_lng, zoom, offset_x, offset_y)
        x2, y2 = coordinates_to_pixel(lat2, lng2, min_lat, max_lat, min_lng, max_lng, zoom, offset_x, offset_y)
        pygame.draw.line(screen, (220, 220, 220), (x1, y1), (x2, y2), 1)


def interpolate_position(G, path, start_time, end_time, current_time):
    if not path or len(path) < 2:
        return None

    total_time = (end_time - start_time).total_seconds()
    elapsed = max(0, (current_time - start_time).total_seconds())
    progress = min(elapsed / total_time, 1.0)

    total_length = 0
    edges = []
    for i in range(len(path) - 1):
        u, v = path[i], path[i + 1]
        if isinstance(G[u][v], dict):
            edge_data = list(G[u][v].values())[0]
        else:
            edge_data = G[u][v]
        length = float(edge_data.get("length", 1.0))
        total_length += length
        edges.append((u, v, length))

    dist_traveled = progress * total_length
    for u, v, length in edges:
        if dist_traveled > length:
            dist_traveled -= length
        else:
            lat1, lng1 = float(G.nodes[u]["y"]), float(G.nodes[u]["x"])
            lat2, lng2 = float(G.nodes[v]["y"]), float(G.nodes[v]["x"])
            ratio = dist_traveled / length if length > 0 else 0
            lat = lat1 + (lat2 - lat1) * ratio
            lng = lng1 + (lng2 - lng1) * ratio
            return lat, lng

    return float(G.nodes[path[-1]]["y"]), float(G.nodes[path[-1]]["x"])


def nearest_node(G, lat, lng):
    nearest = None
    min_dist = float("inf")
    for node, data in G.nodes(data=True):
        y, x = float(data["y"]), float(data["x"])
        dist = (y - lat) ** 2 + (x - lng) ** 2
        if dist < min_dist:
            min_dist = dist
            nearest = node
    return nearest


# ---------------- LOAD GRAPH -----------------
print("Loading graph...")
G = nx.read_graphml(MANHATTAN_GRAPH_FILE)

for u, v, data in G.edges(data=True):
    if "length" in data:
        data["length"] = float(data["length"])

lats = [float(data["y"]) for _, data in G.nodes(data=True)]
lngs = [float(data["x"]) for _, data in G.nodes(data=True)]
min_lat, max_lat = min(lats), max(lats)
min_lng, max_lng = min(lngs), max(lngs)

# Add padding
lat_padding = (max_lat - min_lat) * 0.02
lng_padding = (max_lng - min_lng) * 0.02
min_lat -= lat_padding
max_lat += lat_padding
min_lng -= lng_padding
max_lng += lng_padding

# ---------------- LOAD TRIPS -----------------
bike_trips = []
with open(BIKE_DATA_FILE, newline='') as f:
    reader = csv.DictReader(f)
    for row in reader:
        row["started_at"] = datetime.strptime(row["started_at"], "%Y-%m-%d %H:%M:%S.%f")
        row["ended_at"] = datetime.strptime(row["ended_at"], "%Y-%m-%d %H:%M:%S.%f")
        bike_trips.append(row)

valid_trips = []
for trip in bike_trips[:NUMBER_OF_TRIPS]:
    if not trip["start_lat"] or not trip["start_lng"] or not trip["end_lat"] or not trip["end_lng"]:
        continue
    trip["start_lat"] = float(trip["start_lat"])
    trip["start_lng"] = float(trip["start_lng"])
    trip["end_lat"] = float(trip["end_lat"])
    trip["end_lng"] = float(trip["end_lng"])
    valid_trips.append(trip)

bike_trips = valid_trips
print(f"{len(bike_trips)} valid trips loaded.")

# ---------------- PRECOMPUTE NODES -----------------
print("Precomputing nearest nodes...")
for trip in bike_trips:
    trip["start_node"] = nearest_node(G, trip["start_lat"], trip["start_lng"])
    trip["end_node"] = nearest_node(G, trip["end_lat"], trip["end_lng"])

# ---------------- CACHE PATHS -----------------
print("Caching shortest paths...")
path_cache = {}
for trip in bike_trips:
    key = (trip["start_node"], trip["end_node"])
    if key in path_cache:
        trip["path"] = path_cache[key]
    else:
        try:
            path = nx.shortest_path(G, trip["start_node"], trip["end_node"], weight="length")
            path_cache[key] = path
            trip["path"] = path
        except nx.NetworkXNoPath:
            trip["path"] = None

# ---------------- PYGAME SETUP -----------------
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Manhattan Bike Trips")
font = pygame.font.SysFont("Arial", 18)
clock = pygame.time.Clock()

current_time = bike_trips[0]["started_at"]
already_started_index = 0
active_trips = []

zoom = 1.0
offset_x, offset_y = 0, 0
dragging = False
drag_start = (0, 0)

# ---------------- SIMULATION LOOP -----------------
running = True
while running and current_time < max(trip["ended_at"] for trip in bike_trips):
    dt = clock.get_time() / 1000.0  # seconds since last frame

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                SIMULATION_SPEED *= 2
            elif event.key == pygame.K_DOWN:
                SIMULATION_SPEED /= 2
            elif event.key == pygame.K_r:
                SIMULATION_SPEED = 1.0
        elif event.type == pygame.MOUSEWHEEL:
            if event.y > 0:
                zoom *= 1.1
            elif event.y < 0:
                zoom /= 1.1
            zoom = max(0.1, min(zoom, 10))
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                dragging = True
                drag_start = pygame.mouse.get_pos()
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                dragging = False
        elif event.type == pygame.MOUSEMOTION and dragging:
            mx, my = pygame.mouse.get_pos()
            dx, dy = mx - drag_start[0], my - drag_start[1]
            offset_x += dx
            offset_y += dy
            drag_start = (mx, my)

    # Start new trips
    for trip_index in range(already_started_index, len(bike_trips)):
        trip = bike_trips[trip_index]
        if is_ongoing(current_time, trip["started_at"], trip["ended_at"]):
            active_trips.append(trip)
            already_started_index = trip_index + 1
        elif trip["started_at"] > current_time:
            break

    # Remove finished trips
    active_trips = [trip for trip in active_trips if trip["ended_at"] >= current_time]

    # Advance simulation time in real-time
    current_time += timedelta(seconds=dt * SIMULATION_SPEED)

    # ---------------- DRAW -----------------
    screen.fill((0, 0, 0))
    draw_graph(screen, G, min_lat, max_lat, min_lng, max_lng, zoom, offset_x, offset_y)

    for trip in active_trips:
        if not trip.get("path"):
            continue
        pos = interpolate_position(G, trip["path"], trip["started_at"], trip["ended_at"], current_time)
        if pos is None:
            continue
        lat, lng = pos
        x, y = coordinates_to_pixel(lat, lng, min_lat, max_lat, min_lng, max_lng, zoom, offset_x, offset_y)
        if 0 <= x <= SCREEN_WIDTH and 0 <= y <= SCREEN_HEIGHT:
            color = (250, 0, 0)
            if trip["rideable_type"] == "electric_bike":
                color = (0, 250, 0)
            pygame.draw.circle(screen, color, (x, y), 3)

    # HUD info
    active_text = font.render(f"Active bikes: {len(active_trips)}", True, (255, 255, 255))
    time_text = font.render(f"Time: {current_time.strftime('%Y-%m-%d %H:%M:%S')}", True, (255, 255, 255))
    speed_text = font.render(f"Speed: x{SIMULATION_SPEED:.1f}", True, (255, 255, 255))
    hint_text = font.render(f"[↑/↓ speed | R reset | scroll zoom | drag pan]", True, (180, 180, 180))

    screen.blit(active_text, (10, 10))
    screen.blit(time_text, (10, 30))
    screen.blit(speed_text, (10, 50))
    screen.blit(hint_text, (10, 670))

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
