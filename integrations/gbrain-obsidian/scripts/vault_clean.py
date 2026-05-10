#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from maintenance.vault_cleaner import find_raw_content_sections


if __name__ == "__main__":
    matches = find_raw_content_sections()
    if not matches:
        print("PASS: no raw content sections found")
    else:
        print("WARN: raw content sections found")
        for match in matches:
            print(match)

