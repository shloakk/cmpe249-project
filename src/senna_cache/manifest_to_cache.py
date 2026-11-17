"""Convert a manifest to a GT-only action cache for C1/C2/C3 training."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    samples = json.loads(args.manifest.read_text())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w") as handle:
        for sample in samples:
            handle.write(json.dumps({
                "schema_version": 1,
                "token": str(sample["token"]),
                "gt_speed": sample["gt_speed"],
                "gt_path": sample["gt_path"],
                "pred_speed": None,
                "pred_path": None,
                "parse_ok": False,
                "source": "manifest_ground_truth",
            }, sort_keys=True) + "\n")
    print(json.dumps({"samples": len(samples), "output": str(args.output)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
