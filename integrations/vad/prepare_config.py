"""Install the additive VAD integration and make a condition-specific config."""
from __future__ import annotations

import argparse
import ast
from pathlib import Path
import shutil
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
    parser.add_argument("--condition", choices=("c1", "c2", "c3", "real"), required=True)
    parser.add_argument("--cache", type=Path, required=True)
    parser.add_argument("--audit", type=Path)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--uniform-probability", type=float, default=0.0)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--base-config", default="projects/configs/VAD/VAD_tiny_stage_2.py")
    args = parser.parse_args()
    root = args.vad_root.resolve()
    revision = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True
    ).strip()
    if revision != PINNED_VAD:
        raise SystemExit(f"expected VAD {PINNED_VAD}, found {revision}")
    destination = root / "projects/mmdet3d_plugin/VAD/conditioned_vad_head.py"
    shutil.copy2(Path(__file__).with_name("conditioned_vad_head.py"), destination)
    shutil.copy2(
        Path(__file__).with_name("conditioned_vad.py"),
        destination.with_name("conditioned_vad.py"),
    )
    init = destination.with_name("__init__.py")
    init_text = init.read_text()
    imports = (
        "from .conditioned_vad_head import ConditionedVADHead\n"
        "from .conditioned_vad import ConditionedVAD\n"
    )
    if "from .conditioned_vad_head import ConditionedVADHead" not in init_text:
        init.write_text(init_text + "\n" + imports)

    base = (root / args.base_config).resolve()
    text = absolutize_base_paths(base.read_text(), base)
    data_root_line = "data_root = 'data/nuscenes/'"
    if text.count(data_root_line) != 1:
        raise SystemExit(f"expected exactly one {data_root_line!r} in {base}")
    data_root = str(args.data_root.resolve()).rstrip("/") + "/"
    text = text.replace(data_root_line, f"data_root = {data_root!r}", 1)
    detector = "type='VAD',"
    if text.count(detector) != 1:
        raise SystemExit(f"expected exactly one {detector!r} in {base}")
    text = text.replace(detector, "type='ConditionedVAD',\n    train_adapter_only=True,", 1)
    needle = "type='VADHead',"
    if text.count(needle) != 1:
        raise SystemExit(f"expected exactly one {needle!r} in {base}")
    audit = str(args.audit.resolve()) if args.audit else ""
    replacement = (
        "type='ConditionedVADHead',\n"
        "        meta_action_cfg=dict(\n"
        f"            condition='{args.condition}',\n"
        f"            cache_path={str(args.cache.resolve())!r},\n"
        f"            confusion_path={audit!r},\n"
        f"            uniform_probability={args.uniform_probability!r},\n"
        "            seed=249, embedding_dim=32),"
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    text = text.replace(needle, replacement)
    # The training cache intentionally contains train tokens only. Final
    # comparison uses the separately generated `real` validation config.
    text += "\n# Adapter runs are evaluated in a separate controlled job.\nevaluation = None\n"
    args.output.write_text(text)
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
