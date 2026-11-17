"""Dependency-free path validation; never creates or modifies dataset files."""
import json
import os
from pathlib import Path
import sys

NAMES = (
    "NUSCENES_DATA_ROOT", "NUSCENES_DERIVED_ROOT", "EXPERIMENT_ROOT",
    "SENNA_CHECKPOINT_ROOT", "HF_HOME",
)


def validate_paths(env=None):
    env = os.environ if env is None else env
    paths = {}
    for name in NAMES:
        raw = env.get(name, "")
        if not raw.strip() or "<" in raw or ">" in raw:
            raise ValueError(f"{name}: set an absolute path in the ignored .env file")
        path = Path(raw).expanduser()
        if not path.is_absolute():
            raise ValueError(f"{name}: expected an absolute path")
        if not path.is_dir():
            raise ValueError(f"{name}: directory does not exist: {path}")
        if not os.access(path, os.R_OK | os.X_OK):
            raise ValueError(f"{name}: directory is not readable/searchable: {path}")
        paths[name] = path.resolve()
    data = paths["NUSCENES_DATA_ROOT"]
    derived = paths["NUSCENES_DERIVED_ROOT"]
    artifact = paths["EXPERIMENT_ROOT"]
    for name in ("EXPERIMENT_ROOT", "SENNA_CHECKPOINT_ROOT", "HF_HOME"):
        path = paths[name]
        for protected in (data, derived):
            if path == protected or protected in path.parents or path in protected.parents:
                raise ValueError(f"{name}: writable and shared roots must not overlap")
        if name != "EXPERIMENT_ROOT" and artifact not in path.parents:
            raise ValueError(f"{name}: must be inside EXPERIMENT_ROOT")
        if not os.access(path, os.W_OK | os.X_OK):
            raise ValueError(f"{name}: directory is not writable: {path}")
    for directory in ("samples", "sweeps", "maps", "v1.0-trainval"):
        if not (data / directory).is_dir():
            raise ValueError(f"NUSCENES_DATA_ROOT: missing directory {directory}")
    return paths


def main():
    try:
        print(json.dumps({k: str(v) for k, v in validate_paths().items()}, indent=2))
    except ValueError as error:
        print(f"Configuration error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
