#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from maintenance.gbrain_maintain import run_maintenance


if __name__ == "__main__":
    for result in run_maintenance():
        print(result)

