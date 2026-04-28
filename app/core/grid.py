import numpy as np


def create_grid(min_lat, max_lat, min_lon, max_lon, step=0.2):
    grid = []

    lat_points = np.arange(min_lat, max_lat, step)
    lon_points = np.arange(min_lon, max_lon, step)

    for lat in lat_points:
        for lon in lon_points:
            grid.append({
                "lat": lat,
                "lon": lon
            })

    return grid
