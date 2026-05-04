import numpy as np
import pandas as pd
import requests
import time

lats = np.arange(8, 13, 0.5)
lons = np.arange(76, 80, 0.5)
API_KEY = "76a95118ccc9061932437c07d75f5016"
all_data = []

for lat in lats:
    for lon in lons:
        url = f"https://power.larc.nasa.gov/{API_KEY}/temporal/daily/point"

        params = {
            "parameters": "T2M,PRECTOT,WS2M,RH2M",
            "start": "20250101",
            "end": "20251231",
            "latitude": lat,
            "longitude": lon,
            "format": "JSON"
        }

        res = requests.get(url, params=params)

        # ✅ Check response
        if res.status_code != 200:
            print(f"❌ Failed for {lat},{lon}")
            continue

        json_data = res.json()

        # ✅ Check if correct data exists
        if "properties" not in json_data:
            print(f"⚠️ No data for {lat},{lon}")
            print(json_data)  # debug
            continue

        data = json_data["properties"]["parameter"]

        df = pd.DataFrame({
            "date": list(data["T2M"].keys()),
            "temp": list(data["T2M"].values()),
            "rain": list(data["PRECTOT"].values()),
            "wind": list(data["WS2M"].values()),
            "humidity": list(data["RH2M"].values()),
            "lat": lat,
            "lon": lon
        })

        all_data.append(df)

        print(f"✅ Done: {lat},{lon}")

        time.sleep(0.5)  # avoid rate limit

# ✅ Combine all
weather_df = pd.concat(all_data, ignore_index=True)
weather_df.to_csv("tn_weather_1year.csv", index=False)

print("🎉 Tamil Nadu weather data ready!")