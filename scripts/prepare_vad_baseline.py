"""Copy the pinned VAD baseline config with an absolute data root."""
from __future__ import annotations

import argparse
import ast
from pathlib import Path
import subprocess

PINNED_VAD = "1688c4b1c3a9e2e7873ca9700ff8058170c0e3c8"


def absolutize_base_paths(text: str, source: Path) -> str:
    """Make MMCV ``_base_`` paths independent of the output location."""
    tree = ast.parse(text, filename=str(source))
    matches = []
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if any(isinstance(target, ast.Name) and target.id == "_base_"
               for target in node.targets):
            matches.append(node)
    if len(matches) != 1:
        raise SystemExit(f"expected exactly one _base_ assignment in {source}")
    node = matches[0]
    value = ast.literal_eval(node.value)
    if isinstance(value, str):
        resolved = str((source.parent / value).resolve())
    elif isinstance(value, (list, tuple)) and all(
            isinstance(item, str) for item in value):
        resolved = [str((source.parent / item).resolve()) for item in value]
    else:
        raise SystemExit(f"unsupported _base_ value in {source}")
    lines = text.splitlines(keepends=True)
    replacement = f"_base_ = {resolved!r}\n"
    lines[node.lineno - 1:node.end_lineno] = [replacement]
    return "".join(lines)


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
    text = absolutize_base_paths(source.read_text(), source)
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
