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
        condition_root = args.root / condition
        paths = sorted(condition_root.glob("*/planning_metrics.json"))
        legacy = condition_root / "planning_metrics.json"
        if legacy.is_file():
            paths.insert(0, legacy)
        for path in paths:
            metrics = json.loads(path.read_text())
            run_id = "legacy" if path == legacy else path.parent.name
            rows.append({
                "condition": condition,
                "run_id": run_id,
                **{key: metrics.get(key) for key in KEYS},
            })
    if not rows:
        raise SystemExit(f"no planning_metrics.json files found below {args.root}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=("condition", "run_id", *KEYS))
        writer.writeheader()
        writer.writerows(rows)
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
