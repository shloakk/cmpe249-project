"""Run released Senna-VLM deterministically and write resumable JSONL cache."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
import time
from types import SimpleNamespace

from src.meta_actions import parse_prediction


def completed_tokens(path: Path) -> set[str]:
    if not path.exists():
        return set()
    tokens = set()
    with path.open() as handle:
        for line in handle:
            try:
                tokens.add(str(json.loads(line)["token"]))
            except (json.JSONDecodeError, KeyError):
                continue
    return tokens


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--senna-root", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--max-new-tokens", type=int, default=64)
    args = parser.parse_args()

    if not args.checkpoint.is_dir():
        raise SystemExit(f"checkpoint directory not found: {args.checkpoint}")
    sys.path.insert(0, str(args.senna_root.resolve()))
    from data_tools.senna_qa_utils import eval_multi_img_model_wo_init
    from llava.model.builder import load_senna_pretrained_model

    samples = json.loads(args.manifest.read_text())
    if args.limit:
        samples = samples[: args.limit]
    done = completed_tokens(args.output)
    args.output.parent.mkdir(parents=True, exist_ok=True)

    tokenizer, model, image_processor, _ = load_senna_pretrained_model(
        str(args.checkpoint), None, model_name="llava", device_map=0
    )
    metadata = {
        "checkpoint": str(args.checkpoint.resolve()),
        "senna_root": str(args.senna_root.resolve()),
        "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES"),
    }
    with args.output.open("a", buffering=1) as output:
        for position, sample in enumerate(samples, start=1):
            token = str(sample["token"])
            if token in done:
                continue
            inference_args = SimpleNamespace(
                model_path=str(args.checkpoint), model_base=None,
                query=sample["question"], conv_mode="llava_v1",
                image_file=sample["images"], sep=",", temperature=0,
                top_p=None, num_beams=1, max_new_tokens=args.max_new_tokens,
            )
            started = time.perf_counter()
            raw = eval_multi_img_model_wo_init(
                inference_args, tokenizer, model, image_processor
            )
            elapsed = time.perf_counter() - started
            pred_speed, pred_path = parse_prediction(raw)
            row = {
                "schema_version": 1,
                "token": token,
                "gt_speed": sample["gt_speed"],
                "gt_path": sample["gt_path"],
                "pred_speed": pred_speed,
                "pred_path": pred_path,
                "parse_ok": pred_speed is not None and pred_path is not None,
                "raw_prediction": raw,
                "latency_seconds": elapsed,
                "current_speed_mps": sample.get("current_speed_mps"),
                "navigation_command": sample.get("navigation_command"),
                "route_command_source": sample.get("route_command_source"),
                "run": metadata,
            }
            output.write(json.dumps(row, sort_keys=True) + "\n")
            print(f"[{position}/{len(samples)}] {token} {raw!r} {elapsed:.2f}s", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
