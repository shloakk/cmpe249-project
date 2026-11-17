"""Build a Senna evaluation manifest from a VAD-style nuScenes info pickle."""
from __future__ import annotations

import argparse
import json
import pickle
from pathlib import Path
from typing import Any

import numpy as np

from src.meta_actions import (
    CAMERA_ORDER, navigation_command, path_label, planning_prompt, speed_label,
)


def _records(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ("infos", "data_list"):
            if isinstance(payload.get(key), list):
                return payload[key]
    raise ValueError("annotation must be a list or a dict containing infos/data_list")


def _camera_path(record: dict[str, Any], camera: str, data_root: Path) -> str:
    cameras = record.get("cams") or record.get("images") or {}
    entry = cameras.get(camera)
    if not isinstance(entry, dict):
        raise ValueError(f"missing camera {camera}")
    raw = entry.get("data_path") or entry.get("img_path") or entry.get("filename")
    if not raw:
        raise ValueError(f"missing image path for {camera}")
    path = Path(str(raw))
    if not path.is_absolute():
        # Old VAD pickles may prefix paths with ./data/nuscenes/.
        parts = path.parts
        if "samples" in parts:
            path = data_root.joinpath(*parts[parts.index("samples"):])
        elif "sweeps" in parts:
            path = data_root.joinpath(*parts[parts.index("sweeps"):])
        else:
            path = data_root / path
    return str(path.resolve())


def _trajectory(record: dict[str, Any]) -> list[list[float]]:
    raw = record.get("gt_ego_fut_trajs")
    if raw is None:
        raise ValueError("missing gt_ego_fut_trajs")
    array = np.asarray(raw, dtype=float).reshape(-1, 2)
    mask = record.get("gt_ego_fut_masks")
    if mask is not None:
        valid = np.asarray(mask).reshape(-1).astype(bool)
        if not valid.all():
            raise ValueError("future trajectory contains invalid steps")
        array = array[: len(valid)][valid[: len(array)]]
    if len(array) < 2:
        raise ValueError("fewer than two valid future trajectory steps")
    # VAD stores offsets; Senna's label functions expect cumulative positions.
    return np.cumsum(array, axis=0).tolist()


def _speed(record: dict[str, Any]) -> float:
    if record.get("ego_cur_vel") is not None:
        return float(record["ego_cur_vel"])
    feature = record.get("gt_ego_lcf_feat")
    if feature is not None:
        flat = np.asarray(feature).reshape(-1)
        if len(flat) > 7:
            return float(flat[7])
    velocity = record.get("ego_velocity")
    if velocity is None:
        velocity = record.get("velocity")
    if velocity is not None:
        flat = np.asarray(velocity).reshape(-1)
        return float(np.linalg.norm(flat[:2]))
    return 0.0


def build(annotation: Path, data_root: Path, strict_files: bool = True) -> list[dict]:
    with annotation.open("rb") as handle:
        records = _records(pickle.load(handle))
    manifest = []
    skipped = []
    for index, record in enumerate(records):
        try:
            images = [_camera_path(record, camera, data_root) for camera in CAMERA_ORDER]
            if strict_files:
                missing = [path for path in images if not Path(path).is_file()]
                if missing:
                    raise ValueError(f"missing image: {missing[0]}")
            trajectory = _trajectory(record)
            raw_command = record.get("ego_navi_cmd")
            has_official_command = isinstance(raw_command, str) and bool(raw_command.strip())
            command = (raw_command.strip() if has_official_command else
                       navigation_command(record.get("gt_ego_fut_cmd")))
            speed = _speed(record)
            speed_gt, path_gt = speed_label(trajectory), path_label(trajectory)
            manifest.append({
                "token": str(record.get("token") or record.get("sample_idx") or index),
                "images": images,
                "question": planning_prompt(speed, command),
                "gt_speed": speed_gt,
                "gt_path": path_gt,
                "gt_answer": f"{speed_gt}, {path_gt}",
                "current_speed_mps": speed,
                "navigation_command": command,
                "route_command_source": (
                    "ego_navi_cmd" if has_official_command else
                    "gt_ego_fut_cmd_three_second_fallback"
                ),
            })
        except (KeyError, TypeError, ValueError) as error:
            skipped.append({"index": index, "reason": str(error)})
    if not manifest:
        details = skipped[0]["reason"] if skipped else "no records"
        raise RuntimeError(f"manifest is empty; first error: {details}")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--annotation", type=Path, required=True)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--allow-missing-images", action="store_true")
    args = parser.parse_args()
    manifest = build(args.annotation, args.data_root, not args.allow_missing_images)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"samples": len(manifest), "output": str(args.output)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
