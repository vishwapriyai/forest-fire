import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.grid import create_grid
from ml.inference.predict import predict_risk_frame
from pipelines.processing.build_fire_history import (
    TN_BOUNDS,
    build_recent_fire_outputs,
    hotspot_score_many,
    load_fire_raw,
    synthesize_weather,
)


def risk_band(value):
    if value >= 0.7:
        return "high"
    if value >= 0.4:
        return "medium"
    return "low"


def run(days=5, step=0.25):
    raw = load_fire_raw()
    recent, summary = build_recent_fire_outputs(days=5)
    latest_date = raw["acq_date"].max()

    grid = pd.DataFrame(
        create_grid(
            TN_BOUNDS["min_lat"],
            TN_BOUNDS["max_lat"],
            TN_BOUNDS["min_lon"],
            TN_BOUNDS["max_lon"],
            step=step,
        )
    )

    historical_hotspot = hotspot_score_many(grid["lat"], grid["lon"], raw)
    if len(recent):
        recent_hotspot = hotspot_score_many(grid["lat"], grid["lon"], recent, sigma=0.22)
    else:
        recent_hotspot = np.zeros(len(grid), dtype=float)

    all_days = []
    for day in range(1, days + 1):
        frame = grid.copy()
        target_date = latest_date + pd.Timedelta(days=day)
        frame["forecast_date"] = target_date
        frame["month"] = int(target_date.month)
        frame["day_of_year"] = int(target_date.dayofyear)
        frame["is_daytime"] = 1
        frame["hotspot_score"] = historical_hotspot
        frame["recent_fire_score"] = recent_hotspot * max(0.35, 1 - ((day - 1) * 0.12))

        weather = synthesize_weather(
            frame["lat"],
            frame["lon"],
            pd.Series([target_date] * len(frame)),
            np.clip(frame["hotspot_score"] * 0.65 + frame["recent_fire_score"] * 0.35, 0, 1),
            noise_scale=0.35,
            seed=42 + day,
        )
        frame = pd.concat([frame.reset_index(drop=True), weather], axis=1)

        heuristic = np.clip(
            0.42 * frame["hotspot_score"]
            + 0.33 * frame["recent_fire_score"]
            + 0.25 * frame["seasonal_dryness"],
            0,
            1,
        )
        frame["frp"] = np.clip(2.5 + heuristic * 42, 0, None)
        frame["brightness"] = 305 + heuristic * 52
        frame["scan"] = 0.42 + frame["recent_fire_score"] * 0.28
        frame["track"] = 0.44 + frame["hotspot_score"] * 0.24

        feature_frame = pd.DataFrame(
            {
                "latitude": frame["lat"],
                "longitude": frame["lon"],
                "month": frame["month"],
                "day_of_year": frame["day_of_year"],
                "is_daytime": frame["is_daytime"],
                "frp": frame["frp"],
                "brightness": frame["brightness"],
                "scan": frame["scan"],
                "track": frame["track"],
                "temp_c": frame["temp_c"],
                "humidity": frame["humidity"],
                "wind_kph": frame["wind_kph"],
                "hotspot_score": frame["hotspot_score"],
                "recent_fire_score": frame["recent_fire_score"],
                "seasonal_dryness": frame["seasonal_dryness"],
            }
        )

        model_prob = predict_risk_frame(feature_frame)
        frame["predicted_risk"] = np.clip(model_prob * 0.58 + heuristic * 0.42, 0, 1)
        frame["risk_band"] = frame["predicted_risk"].apply(risk_band)
        frame["day"] = day

        day_output = frame[
            [
                "day",
                "forecast_date",
                "lat",
                "lon",
                "predicted_risk",
                "risk_band",
                "recent_fire_score",
                "hotspot_score",
                "temp_c",
                "humidity",
                "wind_kph",
            ]
        ].copy()
        day_output.to_csv(f"data/processed/grid_predictions_day{day}.csv", index=False)
        all_days.append(day_output)

    combined = pd.concat(all_days, ignore_index=True)
    combined.to_csv("data/processed/tamil_nadu_fire_predictions.csv", index=False)
    combined.loc[combined["day"] == 1].to_csv("data/processed/grid_predictions.csv", index=False)

    features = []
    day1 = combined.loc[combined["day"] == 1]
    for _, row in day1.iterrows():
        features.append(
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [float(row["lon"]), float(row["lat"])],
                },
                "properties": {
                    "day": int(row["day"]),
                    "forecast_date": str(row["forecast_date"])[:10],
                    "predicted_risk": float(row["predicted_risk"]),
                    "risk_band": row["risk_band"],
                    "recent_fire_score": float(row["recent_fire_score"]),
                    "hotspot_score": float(row["hotspot_score"]),
                },
            }
        )

    with open("data/processed/grid_risk.geojson", "w", encoding="utf-8") as f:
        json.dump({"type": "FeatureCollection", "features": features}, f)

    with open("data/processed/prediction_summary.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "latest_observed_date": summary["latest_date"],
                "prediction_days": days,
                "high_risk_cells_day1": int((day1["predicted_risk"] >= 0.7).sum()),
                "average_risk_day1": float(day1["predicted_risk"].mean()),
            },
            f,
        )

    print("Tamil Nadu fire predictions generated")


if __name__ == "__main__":
    run()
