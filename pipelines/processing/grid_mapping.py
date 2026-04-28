import pandas as pd
from app.core.grid import create_grid

def map_fire_to_grid():
    fire = pd.read_csv("data/processed/fire_clean.csv")

    # grid = create_grid(8, 14, 76, 80, step=0.3)
    grid = create_grid(8, 14, 76, 80, step=0.8)

    results = []

    for cell in grid:
        lat, lon = cell["lat"], cell["lon"]

        nearby = fire[
            (abs(fire["latitude"] - lat) < 0.3) &
            (abs(fire["longitude"] - lon) < 0.3)
        ].copy()

        # risk = nearby["confidence"].mean() if not nearby.empty else 0
        confidence_map = {"l": 30, "n": 60, "h": 90}

        if not nearby.empty:
            nearby["confidence_num"] = nearby["confidence"].map(confidence_map)
            # risk = nearby["confidence_num"].mean()
            risk = min(nearby["confidence_num"].mean() / 100, 1)
        else:
            risk = 0

        results.append({
            "lat": lat,
            "lon": lon,
            "fire_risk": risk / 100
        })

    df = pd.DataFrame(results)
    df.to_csv("data/processed/grid_fire.csv", index=False)

    print("✅ Grid fire data created")

if __name__ == "__main__":
    map_fire_to_grid()