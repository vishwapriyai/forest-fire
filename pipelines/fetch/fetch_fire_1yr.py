import pandas as pd
from datetime import datetime, timedelta

API_KEY = "YOUR_API_KEY"

bbox = "76,8,80,13"

start = datetime(2023, 1, 1)
end = datetime(2023, 12, 31)

all_data = []

while start <= end:
    url = f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{API_KEY}/VIIRS_SNPP_NRT/{bbox}/1"

    try:
        df = pd.read_csv(url)

        if not df.empty:
            df["date"] = start.strftime("%Y-%m-%d")
            all_data.append(df)

        print(f"Fetched: {start}")

    except:
        print(f"Skipped: {start}")

    start += timedelta(days=1)

final_df = pd.concat(all_data, ignore_index=True)
final_df.to_csv("tn_fire_1year.csv", index=False)

print("✅ Tamil Nadu fire data (1 year) saved!")