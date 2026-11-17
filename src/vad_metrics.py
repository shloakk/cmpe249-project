"""Aggregate VAD planning metrics directly from tools/test.py --out pickle."""
from __future__ import annotations

import argparse
import json
import pickle
from pathlib import Path


def _number(value):
    if hasattr(value, "item"):
        return float(value.item())
    return float(value)


def aggregate(results: list[dict]) -> dict:
    valid = [row["metric_results"] for row in results
             if row.get("metric_results", {}).get("fut_valid_flag")]
    keys = (
        "plan_L2_1s", "plan_L2_2s", "plan_L2_3s",
        "plan_obj_col_1s", "plan_obj_col_2s", "plan_obj_col_3s",
        "plan_obj_box_col_1s", "plan_obj_box_col_2s", "plan_obj_box_col_3s",
    )
    return {
        "valid_samples": len(valid),
        **{
            key: sum(_number(row[key]) for row in valid) / len(valid)
            if valid else None
            for key in keys
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    with args.input.open("rb") as handle:
        result = aggregate(pickle.load(handle))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
