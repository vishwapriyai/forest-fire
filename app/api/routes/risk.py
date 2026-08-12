# import json
# from pathlib import Path

# import pandas as pd
# from fastapi import APIRouter

# from app.services.refresh_service import ensure_daily_refresh

# router = APIRouter()


# def _read_json(path):
#     with open(path, encoding="utf-8") as f:
#         return json.load(f)


# @router.get("/")
# def get_risk():
#     ensure_daily_refresh()
#     path = Path("data/processed/grid_risk.geojson")
#     if not path.exists():
#         path = Path("data/processed/recent_fire_last5.geojson")
#     return _read_json(path)


# @router.get("/recent")
# def get_recent_fire_risk():
#     ensure_daily_refresh()
#     return _read_json("data/processed/recent_fire_last5.geojson")


# @router.get("/historical")
# def get_historical_risk():
#     ensure_daily_refresh()
#     return _read_json("data/processed/recent_fire_last5.geojson")


# @router.get("/summary")
# def get_recent_fire_summary():
#     ensure_daily_refresh()
#     df = pd.read_csv("data/processed/recent_fire_last5.csv")
#     if df.empty:
#         return {"fire_count": 0, "avg_frp": 0, "max_frp": 0}

#     return {
#         "fire_count": int(len(df)),
#         "avg_frp": float(df["frp"].mean()),
#         "max_frp": float(df["frp"].max()),
#         "latest_date": str(pd.to_datetime(df["acq_date"]).max().date()),
#     }


import json
from pathlib import Path

import pandas as pd
from fastapi import APIRouter

from app.services.refresh_service import ensure_daily_refresh

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parents[3]
DATA_DIR = BASE_DIR / "data" / "processed"


def _read_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


@router.get("/")
def get_risk():
    ensure_daily_refresh()

    path = DATA_DIR / "grid_risk.geojson"

    if not path.exists():
        path = DATA_DIR / "recent_fire_last5.geojson"

    return _read_json(path)


@router.get("/recent")
def get_recent_fire_risk():
    ensure_daily_refresh()
    return _read_json(DATA_DIR / "recent_fire_last5.geojson")


@router.get("/historical")
def get_historical_risk():
    ensure_daily_refresh()
    return _read_json(DATA_DIR / "recent_fire_last5.geojson")


@router.get("/summary")
def get_recent_fire_summary():
    ensure_daily_refresh()

    df = pd.read_csv(DATA_DIR / "recent_fire_last5.csv")

    if df.empty:
        return {"fire_count": 0, "avg_frp": 0, "max_frp": 0}

    return {
        "fire_count": int(len(df)),
        "avg_frp": float(df["frp"].mean()),
        "max_frp": float(df["frp"].max()),
        "latest_date": str(pd.to_datetime(df["acq_date"]).max().date()),
    }