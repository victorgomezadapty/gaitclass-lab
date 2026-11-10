"""Re-download the deposited workbook from Zenodo only if the local copy is missing.

Usage: .venv/bin/python scripts/fetch_data.py
Never overwrites an existing file. Verifies md5 and size after download.
"""
from __future__ import annotations

import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gaitclass_lab import data as D  # noqa: E402


def main() -> None:
    if D.RAW_PATH.exists():
        D.verify_raw()
        print(f"Present and verified: {D.RAW_PATH}")
        return
    D.RAW_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = D.RAW_PATH.with_suffix(".part")
    urllib.request.urlretrieve(D.ZENODO_FILE_URL, tmp)
    tmp.rename(D.RAW_PATH)
    D.verify_raw()
    print(f"Downloaded and verified: {D.RAW_PATH}")


if __name__ == "__main__":
    main()
