"""Fetch exact upstream revisions and verify source provenance."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

LOCK = Path(__file__).resolve().parents[1] / 'configs/upstream-lock.json'


def git(directory, *args):
    return subprocess.check_output(['git', '-C', str(directory), *args], text=True).strip()


def verify(directory, entry):
    if git(directory, 'rev-parse', 'HEAD') != entry['commit']:
        raise ValueError(f'{directory}: unexpected upstream commit; refusing to overwrite')
    if git(directory, 'status', '--porcelain', '--untracked-files=all'):
        raise ValueError(f'{directory}: dirty upstream checkout; preserve and inspect it')
    for name, expected in entry['files'].items():
        if hashlib.sha256((directory / name).read_bytes()).hexdigest() != expected:
            raise ValueError(f'{directory / name}: provenance hash mismatch')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('names', nargs='+', choices=('senna', 'vad', 'mmdetection3d'))
    args = parser.parse_args()
    entries = json.loads(LOCK.read_text())
    args.root.mkdir(parents=True, exist_ok=True)
    for name in args.names:
        entry = entries[name]
        target = args.root / name
        if not target.exists():
            subprocess.run(['git', 'clone', '--filter=blob:none', '--no-checkout',
                            entry['url'], str(target)], check=True)
            subprocess.run(['git', '-C', str(target), 'checkout', '--detach',
                            entry['commit']], check=True)
        verify(target, entry)
        print(f"VERIFIED {name} {entry['commit']}", flush=True)


if __name__ == '__main__':
    main()
