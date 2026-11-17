"""Audit cached Senna predictions and export machine-readable confusion data."""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path

from src.meta_actions import PATH_LABELS, SPEED_LABELS


def _matrix(rows: list[dict], labels: tuple[str, ...], field: str) -> list[list[int]]:
    counts = Counter((row[f"gt_{field}"], row[f"pred_{field}"]) for row in rows)
    return [[counts[(truth, pred)] for pred in labels] for truth in labels]


def _classification(matrix: list[list[int]], labels: tuple[str, ...]) -> dict:
    metrics = {}
    for index, label in enumerate(labels):
        tp = matrix[index][index]
        support = sum(matrix[index])
        predicted = sum(row[index] for row in matrix)
        precision = tp / predicted if predicted else 0.0
        recall = tp / support if support else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        metrics[label] = {
            "precision": precision, "recall": recall, "f1": f1,
            "support": support,
        }
    return metrics


def audit(rows: list[dict]) -> dict:
    valid = [row for row in rows if row.get("parse_ok")]
    speed = _matrix(valid, SPEED_LABELS, "speed")
    path = _matrix(valid, PATH_LABELS, "path")
    total = len(rows)
    both_correct = sum(
        row["gt_speed"] == row["pred_speed"] and row["gt_path"] == row["pred_path"]
        for row in valid
    )
    speed_correct = sum(row["gt_speed"] == row["pred_speed"] for row in valid)
    path_correct = sum(row["gt_path"] == row["pred_path"] for row in valid)
    return {
        "schema_version": 1,
        "samples": total,
        "parsed_samples": len(valid),
        "parse_rate": len(valid) / total if total else 0.0,
        "joint_accuracy_all": both_correct / total if total else 0.0,
        "speed_accuracy_all": speed_correct / total if total else 0.0,
        "path_accuracy_all": path_correct / total if total else 0.0,
        "actual_change_rate": 1.0 - both_correct / len(valid) if valid else 0.0,
        "speed": {
            "labels": SPEED_LABELS, "matrix": speed,
            "per_class": _classification(speed, SPEED_LABELS),
        },
        "path": {
            "labels": PATH_LABELS, "matrix": path,
            "per_class": _classification(path, PATH_LABELS),
        },
        "joint_confusions": [
            {"gt_speed": key[0], "gt_path": key[1], "pred_speed": key[2],
             "pred_path": key[3], "count": count}
            for key, count in Counter(
                (row["gt_speed"], row["gt_path"], row["pred_speed"], row["pred_path"])
                for row in valid
            ).most_common()
        ],
    }


def _write_matrix(path: Path, labels: tuple[str, ...], matrix: list[list[int]]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["ground_truth\\prediction", *labels])
        for label, row in zip(labels, matrix):
            writer.writerow([label, *row])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    rows = [json.loads(line) for line in args.predictions.read_text().splitlines() if line]
    result = audit(rows)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "metrics.json").write_text(json.dumps(result, indent=2) + "\n")
    _write_matrix(args.output_dir / "speed_confusion.csv", SPEED_LABELS,
                  result["speed"]["matrix"])
    _write_matrix(args.output_dir / "path_confusion.csv", PATH_LABELS,
                  result["path"]["matrix"])
    print(json.dumps({key: result[key] for key in (
        "samples", "parse_rate", "joint_accuracy_all", "actual_change_rate"
    )}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
