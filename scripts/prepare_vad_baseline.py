"""Copy the pinned VAD baseline config with an absolute data root."""
from __future__ import annotations

import argparse
from pathlib import Path
import subprocess

PINNED_VAD = "1688c4b1c3a9e2e7873ca9700ff8058170c0e3c8"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vad-root", type=Path, required=True)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    revision = subprocess.check_output(
        ["git", "-C", str(args.vad_root), "rev-parse", "HEAD"], text=True
    ).strip()
    if revision != PINNED_VAD:
        raise SystemExit(f"expected VAD {PINNED_VAD}, found {revision}")
    source = args.vad_root / "projects/configs/VAD/VAD_tiny_stage_2.py"
    text = source.read_text()
    needle = "data_root = 'data/nuscenes/'"
    if text.count(needle) != 1:
        raise SystemExit(f"expected exactly one {needle!r}")
    data_root = str(args.data_root.resolve()).rstrip("/") + "/"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(text.replace(needle, f"data_root = {data_root!r}", 1))
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
