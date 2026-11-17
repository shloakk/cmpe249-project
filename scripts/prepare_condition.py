"""Prepare a VAD config for one adapter condition from audited Senna errors."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vad-root", type=Path, required=True)
    parser.add_argument("--condition", choices=("c1", "c2", "c3", "real"), required=True)
    parser.add_argument("--cache", type=Path, required=True)
    parser.add_argument("--audit", type=Path, required=True)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    audit = json.loads(args.audit.read_text())
    command = [
        sys.executable, "integrations/vad/prepare_config.py",
        "--vad-root", str(args.vad_root), "--condition", args.condition,
        "--cache", str(args.cache), "--audit", str(args.audit),
        "--data-root", str(args.data_root),
        "--uniform-probability", str(audit["actual_change_rate"]),
        "--output", str(args.output),
    ]
    subprocess.run(command, check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
