"""Build the report-ready C0/C1/C2/C3 planning-metrics table."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

KEYS = (
    "plan_L2_1s", "plan_L2_2s", "plan_L2_3s",
    "plan_obj_col_1s", "plan_obj_col_2s", "plan_obj_col_3s",
    "plan_obj_box_col_1s", "plan_obj_box_col_2s", "plan_obj_box_col_3s",
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True,
                        help="Directory containing c0/c1/c2/c3 result folders")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = []
    for condition in ("c0", "c1", "c2", "c3"):
        path = args.root / condition / "planning_metrics.json"
        if path.is_file():
            metrics = json.loads(path.read_text())
            rows.append({"condition": condition, **{key: metrics.get(key) for key in KEYS}})
    if not rows:
        raise SystemExit(f"no planning_metrics.json files found below {args.root}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=("condition", *KEYS))
        writer.writeheader()
        writer.writerows(rows)
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
