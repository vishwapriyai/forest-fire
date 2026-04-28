import os
import time

import pandas as pd
import requests

API_KEY = "76a95118ccc9061932437c07d75f5016"


def fetch_weather():
    fire_df = pd.read_csv("data/raw/fire/fire_raw.csv").head(20)

    weather_data = []

    for _, row in fire_df.iterrows():
        lat = row["latitude"]
        lon = row["longitude"]

        url = (
            "https://api.openweathermap.org/data/2.5/weather"
            f"?lat={lat}&lon={lon}&appid={API_KEY}"
        )

        res = requests.get(url, timeout=30)
        res.raise_for_status()
        payload = res.json()

        weather_data.append({
            "lat": lat,
            "lon": lon,
            "temp": payload["main"]["temp"],
            "humidity": payload["main"]["humidity"],
            "wind": payload["wind"]["speed"]
        })

        time.sleep(1)

    df = pd.DataFrame(weather_data)

    os.makedirs("data/raw/weather", exist_ok=True)
    df.to_csv("data/raw/weather/weather_raw.csv", index=False)

    print("weather_raw.csv created")


if __name__ == "__main__":
    fetch_weather()
