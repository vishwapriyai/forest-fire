# import pandas as pd

# def build_dataset():
#     fire = pd.read_csv("data/processed/fire_clean.csv")
#     weather = pd.read_csv("data/processed/weather_clean.csv")

#     df = fire.merge(weather, left_on=["latitude", "longitude"],
#                     right_on=["lat", "lon"], how="inner")

#     df["label"] = (df["confidence"] > 70).astype(int)

#     df.to_csv("data/training/training_data.csv", index=False)

#     print("Training data created!")

# if __name__ == "__main__":
#     build_dataset()

import pandas as pd
import os

def build_dataset():
    fire = pd.read_csv("data/processed/fire_clean.csv")
    weather = pd.read_csv("data/processed/weather_clean.csv")

    df = fire.merge(weather, left_on=["latitude", "longitude"],
                    right_on=["lat", "lon"], how="inner")

    # ✅ Convert confidence to numeric
    confidence_map = {"l": 30, "n": 60, "h": 90}
    df["confidence_num"] = df["confidence"].map(confidence_map)

    # ✅ Now create label
    df["label"] = (df["confidence_num"] > 50).astype(int)

    # ✅ Create folder if not exists
    os.makedirs("data/training", exist_ok=True)

    df.to_csv("data/training/training_data.csv", index=False)

    print("Training data created!")

if __name__ == "__main__":
    build_dataset()