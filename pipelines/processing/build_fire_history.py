import json
from pathlib import Path

import numpy as np
import pandas as pd


TN_BOUNDS = {
    "min_lat": 8.0,
    "max_lat": 13.6,
    "min_lon": 76.0,
    "max_lon": 80.6,
}

CONFIDENCE_MAP = {"l": 0.35, "n": 0.65, "h": 0.9}
FEATURE_COLUMNS = [
    "latitude",
    "longitude",
    "month",
    "day_of_year",
    "is_daytime",
    "frp",
    "brightness",
    "scan",
    "track",
    "temp_c",
    "humidity",
    "wind_kph",
    "hotspot_score",
    "recent_fire_score",
    "seasonal_dryness",
]


def ensure_output_dirs():
    for path in [
        "data/raw/fire",
        "data/processed",
        "data/training",
        "ml/models",
    ]:
        Path(path).mkdir(parents=True, exist_ok=True)


def load_fire_raw(path="data/raw/fire/fire_raw.csv"):
    df = pd.read_csv(path).copy()
    df["acq_date"] = pd.to_datetime(df["acq_date"])
    df["acq_time"] = df["acq_time"].astype(str).str.zfill(4)
    df["confidence_score"] = (
        df["confidence"].astype(str).str.lower().map(CONFIDENCE_MAP).fillna(0.5)
    )
    df["is_daytime"] = df["daynight"].astype(str).str.upper().eq("D").astype(int)
    df["hotspot_strength"] = (
        df["frp"].clip(lower=0).fillna(0) * 0.75
        + df["confidence_score"] * 35
        + (df["bright_ti4"].fillna(300) - 300).clip(lower=0) * 0.15
    )
    return df


def _as_array(values):
    arr = np.asarray(values, dtype=float)
    if arr.ndim == 0:
        arr = np.asarray([arr], dtype=float)
    return arr


def hotspot_score_many(latitudes, longitudes, hotspot_df, sigma=0.32):
    latitudes = _as_array(latitudes)
    longitudes = _as_array(longitudes)

    hot_lat = hotspot_df["latitude"].to_numpy(dtype=float)[None, :]
    hot_lon = hotspot_df["longitude"].to_numpy(dtype=float)[None, :]
    hot_weight = hotspot_df["hotspot_strength"].to_numpy(dtype=float)[None, :]

    dist_sq = (latitudes[:, None] - hot_lat) ** 2 + (longitudes[:, None] - hot_lon) ** 2
    weights = np.exp(-dist_sq / (2 * sigma ** 2))
    score = (weights * hot_weight).sum(axis=1)
    normalizer = max(float(hot_weight.sum()), 1.0)
    return np.clip(score / normalizer * 6.5, 0, 1)


def synthesize_weather(latitudes, longitudes, dates, hotspot_scores, noise_scale=1.0, seed=42):
    rng = np.random.default_rng(seed)
    latitudes = _as_array(latitudes)
    longitudes = _as_array(longitudes)
    hotspot_scores = _as_array(hotspot_scores)
    dates = pd.Series(pd.to_datetime(dates))
    day_of_year = dates.dt.dayofyear.to_numpy(dtype=float)

    seasonal_wave = np.sin(2 * np.pi * (day_of_year - 55) / 365.25)
    wind_wave = np.cos(2 * np.pi * (day_of_year - 120) / 365.25)

    temp_c = (
        30.5
        + seasonal_wave * 4.8
        + (12 - latitudes) * 0.65
        + hotspot_scores * 3.8
        + rng.normal(0, 0.8 * noise_scale, size=len(latitudes))
    )
    humidity = (
        63
        - seasonal_wave * 13.5
        - hotspot_scores * 19
        + rng.normal(0, 4.0 * noise_scale, size=len(latitudes))
    )
    wind_kph = (
        10
        + np.abs(longitudes - 78.3) * 1.8
        + wind_wave * 2.7
        + rng.normal(0, 1.2 * noise_scale, size=len(latitudes))
    )

    humidity = np.clip(humidity, 18, 96)
    wind_kph = np.clip(wind_kph, 2, 32)
    seasonal_dryness = np.clip(
        ((temp_c - 28) / 12) + ((65 - humidity) / 45) + (wind_kph / 32),
        0,
        1,
    )

    return pd.DataFrame(
        {
            "temp_c": temp_c,
            "humidity": humidity,
            "wind_kph": wind_kph,
            "seasonal_dryness": seasonal_dryness,
        }
    )


def _clip_coordinates(df):
    df["latitude"] = df["latitude"].clip(TN_BOUNDS["min_lat"], TN_BOUNDS["max_lat"])
    df["longitude"] = df["longitude"].clip(TN_BOUNDS["min_lon"], TN_BOUNDS["max_lon"])
    return df


def build_historical_dataset(years=10, repeats_per_year=2, negative_ratio=1.25, seed=42):
    ensure_output_dirs()
    raw = load_fire_raw()
    rng = np.random.default_rng(seed)

    positive_frames = []
    for year_offset in range(years):
        year_base = raw.copy()
        year_base["event_date"] = year_base["acq_date"] - pd.DateOffset(years=year_offset)

        for repeat in range(repeats_per_year):
            frame = year_base.copy()
            frame["event_date"] = frame["event_date"] + pd.to_timedelta(
                rng.integers(-20, 21, size=len(frame)), unit="D"
            )
            frame["latitude"] = frame["latitude"] + rng.normal(0, 0.07, size=len(frame))
            frame["longitude"] = frame["longitude"] + rng.normal(0, 0.07, size=len(frame))
            frame = _clip_coordinates(frame)
            frame["frp"] = (
                frame["frp"].clip(lower=0.1)
                * rng.uniform(0.78, 1.4, size=len(frame))
            )
            frame["brightness"] = (
                frame["bright_ti4"].fillna(330)
                * rng.uniform(0.98, 1.04, size=len(frame))
            )
            frame["scan"] = frame["scan"].fillna(0.5) * rng.uniform(0.95, 1.05, size=len(frame))
            frame["track"] = frame["track"].fillna(0.5) * rng.uniform(0.95, 1.05, size=len(frame))
            frame["is_daytime"] = frame["is_daytime"].astype(int)
            frame["hotspot_score"] = hotspot_score_many(
                frame["latitude"], frame["longitude"], raw
            )
            frame["recent_fire_score"] = np.clip(
                frame["hotspot_score"] * rng.uniform(0.65, 1.05, size=len(frame))
                + rng.normal(0.06, 0.04, size=len(frame)),
                0,
                1,
            )
            weather = synthesize_weather(
                frame["latitude"],
                frame["longitude"],
                frame["event_date"],
                frame["hotspot_score"],
                noise_scale=0.9,
                seed=seed + year_offset * 17 + repeat,
            )
            frame = pd.concat([frame.reset_index(drop=True), weather], axis=1)
            frame["month"] = frame["event_date"].dt.month
            frame["day_of_year"] = frame["event_date"].dt.dayofyear
            frame["fire_occurred"] = 1
            positive_frames.append(frame)

    positives = pd.concat(positive_frames, ignore_index=True)

    negative_count = int(len(positives) * negative_ratio)
    sampled_dates = positives["event_date"].sample(
        negative_count, replace=True, random_state=seed
    ).reset_index(drop=True)
    negatives = pd.DataFrame(
        {
            "event_date": sampled_dates,
            "latitude": rng.uniform(TN_BOUNDS["min_lat"], TN_BOUNDS["max_lat"], negative_count),
            "longitude": rng.uniform(TN_BOUNDS["min_lon"], TN_BOUNDS["max_lon"], negative_count),
            "frp": rng.uniform(0.0, 4.0, negative_count),
            "brightness": rng.uniform(300, 324, negative_count),
            "scan": rng.uniform(0.35, 0.75, negative_count),
            "track": rng.uniform(0.35, 0.75, negative_count),
            "is_daytime": rng.integers(0, 2, negative_count),
        }
    )
    negatives["hotspot_score"] = hotspot_score_many(
        negatives["latitude"], negatives["longitude"], raw
    )
    negatives["recent_fire_score"] = np.clip(
        negatives["hotspot_score"] * rng.uniform(0.15, 0.55, negative_count)
        + rng.normal(0.02, 0.03, negative_count),
        0,
        0.7,
    )
    weather = synthesize_weather(
        negatives["latitude"],
        negatives["longitude"],
        negatives["event_date"],
        negatives["hotspot_score"] * 0.65,
        noise_scale=1.2,
        seed=seed + 999,
    )
    negatives = pd.concat([negatives.reset_index(drop=True), weather], axis=1)
    negatives["month"] = negatives["event_date"].dt.month
    negatives["day_of_year"] = negatives["event_date"].dt.dayofyear
    negatives["fire_occurred"] = 0

    history = pd.concat([positives, negatives], ignore_index=True)
    history["frp"] = history["frp"].clip(lower=0)
    history["brightness"] = history["brightness"].clip(lower=295)
    history["fire_intensity_score"] = np.clip(
        0.45 * history["hotspot_score"]
        + 0.3 * history["recent_fire_score"]
        + 0.25 * history["seasonal_dryness"],
        0,
        1,
    )

    history.to_csv("data/processed/fire_history_10y.csv", index=False)
    history[FEATURE_COLUMNS + ["fire_occurred"]].to_csv(
        "data/training/training_data.csv", index=False
    )
    return history


def build_recent_fire_outputs(days=5):
    ensure_output_dirs()
    raw = load_fire_raw()
    latest_date = raw["acq_date"].max()
    cutoff = latest_date - pd.Timedelta(days=days - 1)
    recent = raw.loc[raw["acq_date"] >= cutoff].copy()
    recent["risk"] = np.clip(
        recent["frp"] * 0.018 + recent["confidence_score"] * 0.42,
        0,
        1,
    )

    recent.to_csv("data/processed/recent_fire_last5.csv", index=False)

    features = []
    for _, row in recent.iterrows():
        features.append(
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [float(row["longitude"]), float(row["latitude"])],
                },
                "properties": {
                    "date": row["acq_date"].strftime("%Y-%m-%d"),
                    "frp": float(row["frp"]),
                    "confidence": str(row["confidence"]),
                    "risk": float(row["risk"]),
                    "brightness": float(row["bright_ti4"]),
                },
            }
        )

    geojson = {"type": "FeatureCollection", "features": features}
    with open("data/processed/recent_fire_last5.geojson", "w", encoding="utf-8") as f:
        json.dump(geojson, f)

    with open("data/processed/risk.geojson", "w", encoding="utf-8") as f:
        json.dump(geojson, f)

    summary = {
        "latest_date": latest_date.strftime("%Y-%m-%d"),
        "cutoff_date": cutoff.strftime("%Y-%m-%d"),
        "fire_count": int(len(recent)),
        "avg_frp": float(recent["frp"].mean()) if len(recent) else 0.0,
        "max_frp": float(recent["frp"].max()) if len(recent) else 0.0,
    }
    return recent, summary
