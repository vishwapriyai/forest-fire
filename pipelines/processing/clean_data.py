# import pandas as pd

# def clean_fire():
#     df = pd.read_csv("data/raw/fire/fire_raw.csv")
    
#     df = df[["latitude", "longitude", "confidence"]]
#     df.dropna(inplace=True)

#     df.to_csv("data/processed/fire_clean.csv", index=False)

# def clean_weather():
#     df = pd.read_csv("data/raw/weather/weather_raw.csv")
#     df.dropna(inplace=True)

#     df.to_csv("data/processed/weather_clean.csv", index=False)

# if __name__ == "__main__":
#     clean_fire()
#     clean_weather()

import pandas as pd
import os   # ✅ ADD THIS

def clean_fire():
    df = pd.read_csv("data/raw/fire/fire_raw.csv")
    
    df = df[["latitude", "longitude", "confidence", "frp"]]  # ✅ KEEP FRP
    df.dropna(inplace=True)

    # ✅ CREATE FOLDER
    os.makedirs("data/processed", exist_ok=True)

    df.to_csv("data/processed/fire_clean.csv", index=False)

def clean_weather():
    df = pd.read_csv("data/raw/weather/weather_raw.csv")
    df.dropna(inplace=True)

    # ✅ CREATE FOLDER (safe even if exists)
    os.makedirs("data/processed", exist_ok=True)

    df.to_csv("data/processed/weather_clean.csv", index=False)

if __name__ == "__main__":
    clean_fire()
    clean_weather()