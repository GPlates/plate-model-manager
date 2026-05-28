#!/usr/bin/env python3

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from plate_model_manager.utils.layer_validation import validate_layers_source

MODELS_RAW_DATA_FILE = REPO_ROOT / "config" / "models_raw_data.json"


def main():
    checked_models, issues, base_url = validate_layers_source(str(MODELS_RAW_DATA_FILE))

    if issues:
        print("Layer validation failed:")
        for issue in issues:
            print(f"- {issue}")
        raise SystemExit(1)

    print(f"Layer validation passed for {checked_models} models against {base_url}.")


if __name__ == "__main__":
    main()
