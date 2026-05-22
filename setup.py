"""Idempotent MediaPipe pose model download into models/."""

import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).parent
MODEL_DIR = ROOT / "models"
MODEL_FILE = MODEL_DIR / "pose_landmarker_full.task"
MODEL_URL = "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_full/float16/latest/pose_landmarker_full.task"
EXPECTED_MIN_SIZE = 8_000_000


def main():
    MODEL_DIR.mkdir(exist_ok=True)
    if MODEL_FILE.exists() and MODEL_FILE.stat().st_size >= EXPECTED_MIN_SIZE:
        print(f"Model already present ({MODEL_FILE.stat().st_size:,} bytes) -- skipping.")
        return
    print(f"Downloading {MODEL_URL}")
    print(f"  -> {MODEL_FILE}")
    urllib.request.urlretrieve(MODEL_URL, MODEL_FILE)
    size = MODEL_FILE.stat().st_size
    print(f"Downloaded {size:,} bytes.")
    if size < EXPECTED_MIN_SIZE:
        sys.exit(f"Download succeeded but file is suspiciously small ({size:,} bytes).")


if __name__ == "__main__":
    main()
