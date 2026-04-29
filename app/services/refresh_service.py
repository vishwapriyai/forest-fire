import json
import threading
from datetime import date
from pathlib import Path

from run_fire_refresh import main as run_fire_refresh


ROOT_DIR = Path(__file__).resolve().parents[2]
STATE_FILE = ROOT_DIR / "data" / "processed" / "refresh_state.json"
REQUIRED_FILES = [
    ROOT_DIR / "data" / "processed" / "recent_fire_last5.geojson",
    ROOT_DIR / "data" / "processed" / "grid_predictions_day1.csv",
    ROOT_DIR / "data" / "processed" / "fire_history_10y.csv",
]

_refresh_lock = threading.Lock()


def _read_state():
    if not STATE_FILE.exists():
        return {}

    with open(STATE_FILE, encoding="utf-8") as f:
        return json.load(f)


def _write_state(payload):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f)


def _needs_refresh_today():
    if any(not file_path.exists() for file_path in REQUIRED_FILES):
        return True

    state = _read_state()
    return state.get("last_refresh_date") != date.today().isoformat()


def ensure_daily_refresh():
    if not _needs_refresh_today():
        return False

    with _refresh_lock:
        if not _needs_refresh_today():
            return False

        run_fire_refresh()
        _write_state({"last_refresh_date": date.today().isoformat()})
        return True
