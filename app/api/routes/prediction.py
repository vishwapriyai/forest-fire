import pandas as pd
from fastapi import APIRouter


router = APIRouter()


@router.get("/")
def predict(day: int = 1):
    df = pd.read_csv(f"data/processed/grid_predictions_day{day}.csv")
    return df.to_dict(orient="records")


@router.get("/grid")
def get_prediction_grid(day: int = 1):
    df = pd.read_csv(f"data/processed/grid_predictions_day{day}.csv")
    return df.to_dict(orient="records")


@router.get("/summary")
def get_prediction_summary(day: int = 1):
    df = pd.read_csv(f"data/processed/grid_predictions_day{day}.csv")
    top = df.sort_values("predicted_risk", ascending=False).head(8)
    return {
        "day": day,
        "average_risk": float(df["predicted_risk"].mean()),
        "high_risk_cells": int((df["predicted_risk"] >= 0.7).sum()),
        "top_zones": top.to_dict(orient="records"),
    }


@router.get("/geojson")
def get_prediction_geojson(day: int = 1):
    df = pd.read_csv(f"data/processed/grid_predictions_day{day}.csv")
    features = []
    for _, row in df.iterrows():
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
                },
            }
        )
    return {"type": "FeatureCollection", "features": features}
