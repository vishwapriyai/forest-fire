import json

import pandas as pd

from pipelines.fetch.fetch_fire import fetch_fire


def grid_to_geojson():
    df = pd.read_csv("data/processed/grid_predictions.csv")

    features = []

    for _, row in df.iterrows():
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [row["lon"], row["lat"]]
            },
            "properties": {
                "risk": row["predicted_risk"]
            }
        })

    geojson = {"type": "FeatureCollection", "features": features}

    with open("data/processed/grid_risk.geojson", "w", encoding="utf-8") as f:
        json.dump(geojson, f)

    print("grid_risk.geojson created")


def refresh_historical_geojson():
    fire = fetch_fire()

    confidence_map = {"l": 0.3, "n": 0.6, "h": 0.9}
    fire["confidence_num"] = fire["confidence"].map(confidence_map)
    fire["risk"] = fire["frp"] * 0.7 + fire["confidence_num"] * 100 * 0.3

    features = []
    for _, row in fire.iterrows():
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [row["longitude"], row["latitude"]]
            },
            "properties": {
                "risk": row["risk"],
                "frp": row["frp"]
            }
        })

    geojson = {"type": "FeatureCollection", "features": features}

    with open("data/processed/risk.geojson", "w", encoding="utf-8") as f:
        json.dump(geojson, f)

    print("risk.geojson created")


if __name__ == "__main__":
    refresh_historical_geojson()
