# import requests
# import pandas as pd

# API_KEY = "20ed243fa09bc3ea0c800333c079ab75"

# def fetch_fire():
#     url = f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{API_KEY}/VIIRS_SNPP_NRT/68,6,97,37/1"
    
#     df = pd.read_csv(url)

#     # Convert confidence to numeric
#     confidence_map = {"l": 0.3, "n": 0.6, "h": 0.9}
#     df["confidence_num"] = df["confidence"].map(confidence_map)

#     # Create risk score
#     df["risk"] = (
#         df["frp"] * 0.6 +      # fire strength
#         df["confidence_num"] * 100 * 0.4
#     )

#     return df[["latitude", "longitude", "risk", "frp"]]




import requests
import pandas as pd
import os

API_KEY = "20ed243fa09bc3ea0c800333c079ab75"

def fetch_fire():
    url = f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{API_KEY}/VIIRS_SNPP_NRT/76,8,80,13/5"
    
    df = pd.read_csv(url)

    os.makedirs("data/raw/fire", exist_ok=True)
    df.to_csv("data/raw/fire/fire_raw.csv", index=False)

    print("Fire data saved!")
    return df

if __name__ == "__main__":
    fetch_fire()