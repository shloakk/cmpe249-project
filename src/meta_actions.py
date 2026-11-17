"""Senna speed/path labels, parsing, and deterministic ground-truth rules."""
from __future__ import annotations

import math
import re
from typing import Iterable, Sequence

SPEED_LABELS = ("KEEP", "ACCELERATE", "DECELERATE", "STOP")
PATH_LABELS = (
    "RIGHT_TURN", "RIGHT_CHANGE", "LEFT_TURN", "LEFT_CHANGE", "STRAIGHT"
)
CAMERA_ORDER = (
    "CAM_FRONT", "CAM_FRONT_RIGHT", "CAM_FRONT_LEFT",
    "CAM_BACK", "CAM_BACK_LEFT", "CAM_BACK_RIGHT",
)


def _points(trajectory: Iterable[Sequence[float]]) -> list[tuple[float, float]]:
    result = [(float(point[0]), float(point[1])) for point in trajectory]
    if not result:
        raise ValueError("trajectory must contain at least one point")
    return result


def speed_label(trajectory: Iterable[Sequence[float]], dt: float = 0.5) -> str:
    """Match Senna's released 3-second trajectory-to-speed rule."""
    points = _points(trajectory)
    if len(points) < 2:
        return "STOP"
    velocities = [
        math.hypot(b[0] - a[0], b[1] - a[1]) / dt
        for a, b in zip(points, points[1:])
    ]
    if max(velocities) < 2.0:
        return "STOP"
    difference = velocities[-1] - velocities[0]
    if difference >= 3.0:
        return "ACCELERATE"
    if difference <= -3.0:
        return "DECELERATE"
    return "KEEP"


def path_label(trajectory: Iterable[Sequence[float]]) -> str:
    """Match Senna's released lateral-offset/endpoint-angle path rule."""
    x, y = _points(trajectory)[-1]
    angle_difference = math.degrees(math.atan2(y, x)) - 90.0
    if x > 4.0 and angle_difference <= -5.0:
        return "RIGHT_TURN"
    if x > 4.0 and abs(angle_difference) < 5.0:
        return "RIGHT_CHANGE"
    if x <= -4.0 and angle_difference >= 5.0:
        return "LEFT_TURN"
    if x <= -4.0 and abs(angle_difference) < 5.0:
        return "LEFT_CHANGE"
    return "STRAIGHT"


def parse_prediction(text: str) -> tuple[str | None, str | None]:
    """Parse one unambiguous speed label and path label from model text."""
    normalized = re.sub(r"[^A-Z0-9]+", "_", text.upper()).strip("_")
    padded = f"_{normalized}_"
    speeds = [label for label in SPEED_LABELS if f"_{label}_" in padded]
    paths = [label for label in PATH_LABELS if f"_{label}_" in padded]
    return (
        speeds[0] if len(speeds) == 1 else None,
        paths[0] if len(paths) == 1 else None,
    )


def navigation_command(command: object) -> str:
    """Convert VAD's one-hot route command to Senna prompt wording."""
    try:
        values = [float(value) for value in command]  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return "go straight"
    if not values:
        return "go straight"
    index = max(range(len(values)), key=values.__getitem__)
    # Official VAD convention: right, left, straight.
    return {0: "turn right", 1: "turn left", 2: "go straight"}.get(
        index, "go straight"
    )


def planning_prompt(current_speed: float, command: str) -> str:
    return (
        f"Your current speed is {int(current_speed)} m/s, the navigation command "
        f"is '{command}', based on the understanding of the driving scene and "
        "the navigation information, what is your plan for the next three seconds? "
        "Please answer your SPEED plan and your PATH plan. SPEED includes KEEP, "
        "ACCELERATE and DECELERATE, and STOP, PATH includes STRAIGHT, RIGHT_CHANGE, "
        "LEFT_CHANGE, RIGHT_TURN, LEFT_TURN. For example, a correct answer format "
        "is like 'KEEP, LEFT_CHANGE'."
    )
