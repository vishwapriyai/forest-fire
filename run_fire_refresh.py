from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ml.inference.batch_predict import run as run_prediction_pipeline
from ml.training.prepare_data import prepare
from ml.training.train_model import train
from pipelines.fetch.fetch_fire import fetch_fire
from pipelines.processing.build_fire_history import build_recent_fire_outputs


def ensure_directories():
    for path in [
        "data/raw/fire",
        "data/processed",
        "data/training",
        "ml/models",
    ]:
        Path(path).mkdir(parents=True, exist_ok=True)


def refresh_raw_fire_data():
    try:
        fetch_fire()
        print("Fresh NASA fire data downloaded")
    except Exception as exc:
        raw_file = Path("data/raw/fire/fire_raw.csv")
        if not raw_file.exists():
            raise
        print(f"NASA fetch failed, using cached fire_raw.csv instead: {exc}")


def main():
    ensure_directories()

    print("1/4 Refreshing NASA fire extract")
    refresh_raw_fire_data()

    print("2/4 Building 10-year historical training dataset")
    prepare()
    build_recent_fire_outputs(days=5)

    print("3/4 Training fire model")
    train()

    print("4/4 Generating Tamil Nadu fire predictions")
    run_prediction_pipeline(days=5, step=0.25)

    print("Fire refresh complete")


if __name__ == "__main__":
    main()
