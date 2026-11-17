"""Download the public Senna checkpoint into the configured artifact root."""
from __future__ import annotations

import argparse
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repo-id", default="rb93dett/Senna")
    args = parser.parse_args()
    from huggingface_hub import snapshot_download
    args.output.parent.mkdir(parents=True, exist_ok=True)
    result = snapshot_download(
        repo_id=args.repo_id,
        local_dir=args.output,
        local_dir_use_symlinks=False,
        resume_download=True,
    )
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
