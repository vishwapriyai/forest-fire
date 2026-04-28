import os
import sys
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipelines.processing.build_fire_history import FEATURE_COLUMNS


def train():
    df = pd.read_csv("data/training/training_data.csv")

    X = df[FEATURE_COLUMNS]
    y = df["fire_occurred"]

    model = RandomForestClassifier(
        n_estimators=240,
        max_depth=16,
        min_samples_leaf=3,
        class_weight="balanced_subsample",
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X, y)

    os.makedirs("ml/models", exist_ok=True)
    joblib.dump({"model": model, "features": FEATURE_COLUMNS}, "ml/models/model.pkl")

    print("Model trained and saved")


if __name__ == "__main__":
    train()
