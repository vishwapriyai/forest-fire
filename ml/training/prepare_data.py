import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipelines.processing.build_fire_history import FEATURE_COLUMNS, build_historical_dataset


def prepare():
    history = build_historical_dataset()
    training = history[FEATURE_COLUMNS + ["fire_occurred"]].copy()
    training.to_csv("data/training/training_data.csv", index=False)
    print(f"Training data ready with {len(training)} rows")


if __name__ == "__main__":
    prepare()
