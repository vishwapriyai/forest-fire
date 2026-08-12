import json
import shutil
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FRONTEND_DATA = ROOT / "frontend" / "data"
PROCESSED_DATA = ROOT / "data" / "processed"

def export_predictions_to_json():
    FRONTEND_DATA.mkdir(parents=True, exist_ok=True)
    
    # 1. Copy recent_fire_last5.geojson to frontend/data
    recent_geojson_src = PROCESSED_DATA / "recent_fire_last5.geojson"
    recent_geojson_dest = FRONTEND_DATA / "recent_fire_last5.geojson"
    if recent_geojson_src.exists():
        shutil.copy(recent_geojson_src, recent_geojson_dest)
        print(f"Copied {recent_geojson_src.name} to frontend/data/")
    else:
        print(f"Warning: {recent_geojson_src} not found. Run python run_fire_refresh.py first.")

    # 2. Convert grid_predictions_day1.csv through day5.csv to JSON format
    for day in range(1, 6):
        csv_path = PROCESSED_DATA / f"grid_predictions_day{day}.csv"
        json_path = FRONTEND_DATA / f"grid_predictions_day{day}.json"
        
        if csv_path.exists():
            df = pd.read_csv(csv_path)
            # Convert DF to list of dicts
            records = df.to_dict(orient="records")
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(records, f)
            print(f"Converted {csv_path.name} -> {json_path.name}")
            
            # Generate summary JSON as well
            summary_path = FRONTEND_DATA / f"prediction_summary_day{day}.json"
            top_zones = df.sort_values("predicted_risk", ascending=False).head(8).to_dict(orient="records")
            summary_data = {
                "day": day,
                "average_risk": float(df["predicted_risk"].mean()),
                "high_risk_cells": int((df["predicted_risk"] >= 0.7).sum()),
                "top_zones": top_zones,
            }
            with open(summary_path, "w", encoding="utf-8") as f:
                json.dump(summary_data, f)
            print(f"Generated summary -> {summary_path.name}")
        else:
            print(f"Warning: {csv_path.name} not found. Run prediction pipeline first.")

if __name__ == "__main__":
    export_predictions_to_json()
