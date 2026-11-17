"""Reproducible C1/C2/C3 action selection for controlled experiments."""
from __future__ import annotations

import random
from collections import defaultdict
from typing import Iterable

from src.meta_actions import PATH_LABELS, SPEED_LABELS


def uniform_corruption(
    speed: str, path: str, probability: float, rng: random.Random
) -> tuple[str, str]:
    if rng.random() >= probability:
        return speed, path
    alternatives = [
        (candidate_speed, candidate_path)
        for candidate_speed in SPEED_LABELS
        for candidate_path in PATH_LABELS
        if (candidate_speed, candidate_path) != (speed, path)
    ]
    return rng.choice(alternatives)


class EmpiricalCorruptor:
    """Sample observed joint Senna confusions conditional on the true pair."""

    def __init__(self, confusions: Iterable[dict], seed: int = 249):
        self.rng = random.Random(seed)
        self.tables: dict[tuple[str, str], list[tuple[tuple[str, str], int]]] = defaultdict(list)
        for row in confusions:
            truth = (row["gt_speed"], row["gt_path"])
            prediction = (row["pred_speed"], row["pred_path"])
            count = int(row["count"])
            if count > 0:
                self.tables[truth].append((prediction, count))

    def sample(self, speed: str, path: str) -> tuple[str, str]:
        choices = self.tables.get((speed, path))
        if not choices:
            return speed, path
        return self.rng.choices(
            [choice for choice, _ in choices],
            weights=[weight for _, weight in choices], k=1,
        )[0]
