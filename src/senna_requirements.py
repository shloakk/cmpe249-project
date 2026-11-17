"""Select audited inference packages without changing official version pins."""
import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def normalize(name):
    return re.sub(r'[-_.]+', '-', name).lower()


def project(text, selected):
    pins = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        match = re.fullmatch(r'([A-Za-z0-9_.-]+)==([^\s;]+)', line)
        if not match:
            raise ValueError(f'Expected exact official pin: {line}')
        key = normalize(match[1])
        if key in pins:
            raise ValueError(f'Duplicate official package: {key}')
        pins[key] = line
    requested = [normalize(name) for name in selected]
    if len(requested) != len(set(requested)):
        raise ValueError('Duplicate selected package')
    missing = set(requested) - pins.keys()
    if missing:
        raise ValueError(f'Packages missing official pins: {sorted(missing)}')
    return [pins[name] for name in requested], [pins[name] for name in sorted(pins.keys() - set(requested))]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--upstream', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    lock = json.loads((ROOT / 'configs/upstream-lock.json').read_text())['senna']
    source = args.upstream / 'requirements.txt'
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    if digest != lock['files']['requirements.txt']:
        raise ValueError('Official Senna requirements hash mismatch')
    profile = json.loads((ROOT / 'configs/senna-inference-packages.json').read_text())
    included, excluded = project(source.read_text(), profile['packages'])
    args.output.write_text('# Exact version pins selected from official Senna requirements\n' + '\n'.join(included) + '\n')
    audit = {'source_commit': lock['commit'], 'source_sha256': digest,
             'purpose': profile['purpose'], 'included': included, 'excluded': excluded,
             'deviation': 'Inference-only projection; unavailable aidisdk is not replaced; upstream source unchanged'}
    audit_path = args.output.with_suffix('.audit.json')
    audit_path.write_text(json.dumps(audit, indent=2) + '\n')
    print(json.dumps(audit, indent=2), flush=True)
    print(f'PROFILE_WRITTEN {args.output}; audit={audit_path}', flush=True)


if __name__ == '__main__':
    main()
