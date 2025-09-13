import pygame
import pandas as pd
import networkx as nx
import pickle

# ---------- SETTINGS ----------
GRAPHML_FILE = "data\\manhattan.graphml"
BIKE_DATA_FILE = "data\\trips_200k.pkl"
WIDTH, HEIGHT = 600, 600 # DO NOT CHANGE! ( Data is preprocessed for this size )
FPS = 30
SIM_SPEED = 600           # time multiplier (seconds of data per real second tick at FPS)

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
    x = (lon - MIN_LON) / (MAX_LON - MIN_LON) * WIDTH
    y = HEIGHT - (lat - MIN_LAT) / (MAX_LAT - MIN_LAT) * HEIGHT
    return x, y

# Precompute node positions
positions = {
    n: latlon_to_xy(float(data['y']), float(data['x']))
    for n, data in graph.nodes(data=True)
}

#---------------- LOAD TRIPS ------------------------
trips = None
with open(BIKE_DATA_FILE, "rb") as f:
    trips = pickle.load(f)

GLOBAL_START = pd.to_datetime("2024-01-01 00:00:28.894000")
GLOBAL_END = pd.to_datetime("2024-01-10 00:00:28.894000")


# ---------- INIT PYGAME ----------
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Manhattan Bike Trips")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 18)

zoom = 1.0
offset_x = 0
offset_y = 0
dragging = False
last_mouse_pos = None

def transform_point(x, y):
    tx = (x * zoom) + offset_x
    ty = (y * zoom) + offset_y
    return int(tx), int(ty)

# ---------- BUTTONS ----------
BUTTON_WIDTH = 80
BUTTON_HEIGHT = 20
BUTTON_MARGIN = 10
speed_up_button = pygame.Rect(10, 90, BUTTON_WIDTH, BUTTON_HEIGHT)
slow_down_button = pygame.Rect(100, 90, BUTTON_WIDTH, BUTTON_HEIGHT)

def draw_button(rect, text, color=(180, 180, 180)):
    pygame.draw.rect(screen, color, rect)
    txt_surf = font.render(text, True, (0, 0, 0))
    txt_rect = txt_surf.get_rect(center=rect.center)
    screen.blit(txt_surf, txt_rect)


# ---------- SIMULATION STATE ----------
simulation_running = True
sim_time = GLOBAL_START  # start from earliest start in the data

print("Animation running — close the window to stop.")
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and not simulation_running:
                # restart simulation
                with open(BIKE_DATA_FILE, "rb") as f:
                    trips = pickle.load(f)
                #trips = build_trips()
                sim_time = GLOBAL_START
                simulation_running = True

        elif event.type == pygame.MOUSEWHEEL:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            world_x = (mouse_x - offset_x) / zoom
            world_y = (mouse_y - offset_y) / zoom
            if event.y > 0:
                zoom *= 1.1
            else:
                zoom /= 1.1
            offset_x = mouse_x - world_x * zoom
            offset_y = mouse_y - world_y * zoom

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if speed_up_button.collidepoint(event.pos):
                    SIM_SPEED *= 10
                    print(f"Simulation speed increased to {SIM_SPEED}")
                elif slow_down_button.collidepoint(event.pos):
                    SIM_SPEED = max(1, SIM_SPEED / 10)  # avoid zero
                    print(f"Simulation speed decreased to {SIM_SPEED}")
                else:
                    dragging = True
                    last_mouse_pos = pygame.mouse.get_pos()
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                dragging = False
        elif event.type == pygame.MOUSEMOTION and dragging:
            mx, my = pygame.mouse.get_pos()
            dx = mx - last_mouse_pos[0]
            dy = my - last_mouse_pos[1]
            offset_x += dx
            offset_y += dy
            last_mouse_pos = (mx, my)


    screen.fill((255, 255, 255))

    # draw street graph
    for u, v in graph.edges():
        x1, y1 = transform_point(*positions[u])
        x2, y2 = transform_point(*positions[v])
        pygame.draw.line(screen, (200, 200, 200), (x1, y1), (x2, y2), 1)

    active_bikes = 0

    if simulation_running:
        # advance simulation clock
        sim_time += pd.Timedelta(seconds=(1.0 / FPS) * SIM_SPEED)

        for trip in trips:
            if trip["finished"]:
                continue

            # not started yet
            if sim_time < trip["start_time"]:
                continue

            # if sim_time after end -> mark finished
            if sim_time >= trip["end_time"]:
                trip["finished"] = True
                continue

            # fraction of trip completed by sim_time
            total_progress = (sim_time - trip["start_time"]).total_seconds() / trip["duration"]
            if total_progress >= 1.0:
                trip["finished"] = True
                continue

            # distance along path to place the bike
            dist_along = total_progress * trip["total_length"]

            # walk segments to find the correct segment
            d_acc = 0.0
            placed = False
            for seg_idx, seg_len in trip["segments"]:
                if d_acc + seg_len >= dist_along:
                    # place within this segment
                    seg_t = (dist_along - d_acc) / seg_len
                    x1, y1 = trip["path"][seg_idx]
                    x2, y2 = trip["path"][seg_idx + 1]
                    x = x1 + (x2 - x1) * seg_t
                    y = y1 + (y2 - y1) * seg_t
                    bx, by = transform_point(x, y)
                    color = (0, 200, 0) if 'electric' in trip['type'] else (255, 0, 0)
                    pygame.draw.circle(screen, color, (bx, by), 3)
                    placed = True
                    break
                d_acc += seg_len

            # fallback (shouldn't happen) -> place at last node
            if not placed:
                x, y = trip["path"][-1]
                bx, by = transform_point(x, y)
                color = (0, 200, 0) if 'electric' in trip['type'] else (255, 0, 0)
                pygame.draw.circle(screen, color, (bx, by), 3)

            active_bikes += 1

        # Stop simulation only after we've passed the last end time and no bikes active
        if active_bikes == 0 and sim_time > GLOBAL_END:
            simulation_running = False

    # draw real (simulated) time in top-right
    time_text = font.render(sim_time.strftime("Time: %Y-%m-%d %H:%M:%S"), True, (0, 100, 0))
    active_bikes_text = font.render("Active Bikes: {}".format(str(active_bikes)), True, (0, 100, 0))
    screen.blit(time_text, (0 , 10))
    screen.blit(active_bikes_text, (0 , 50))

    draw_button(speed_up_button, "Speed x10")
    draw_button(slow_down_button, "Slow /10")

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
print("Done.")
