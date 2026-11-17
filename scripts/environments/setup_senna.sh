#!/usr/bin/env bash
set -euo pipefail
repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
cd "$repo"
set -a
source .env
set +a
python_bin=${HOST_PYTHON:-python3}
"$python_bin" -m src.config
mkdir -p "$EXPERIMENT_ROOT/logs"
log="$EXPERIMENT_ROOT/logs/senna-install-$(date -u +%Y%m%dT%H%M%SZ)-$$.log"
exec > >(tee "$log") 2>&1
printf 'Install log: %s\nUTC: ' "$log"; date -u +%FT%TZ
printf 'Host: '; hostname
printf 'Commit: '; git rev-parse HEAD
printf 'Dirty status:\n'; git status --short
printf 'Command: bash scripts/environments/setup_senna.sh\n'
exec 9>"$EXPERIMENT_ROOT/logs/.senna-setup.lock"
flock -n 9 || { echo 'Senna installation or validation already active' >&2; exit 1; }
export PYTHONDONTWRITEBYTECODE=1
export PIP_CACHE_DIR="$EXPERIMENT_ROOT/caches/pip"
export CONDA_PKGS_DIRS="$EXPERIMENT_ROOT/caches/conda-pkgs"
export TMPDIR="$EXPERIMENT_ROOT/tmp"
upstream="$EXPERIMENT_ROOT/upstream"
prefix="$EXPERIMENT_ROOT/environments/senna"
profile="$EXPERIMENT_ROOT/environments/senna-inference.requirements.txt"
command -v conda
conda --version
if ! conda tos --version; then
  printf 'Terms plugin version unavailable through its CLI\n'
fi
"$python_bin" -m src.upstream --root "$upstream" --verify-only senna
if [[ -e "$prefix" ]]; then
  [[ "${RESUME_SENNA_ENV:-0}" == 1 ]] || {
    echo 'Existing prefix preserved. Use RESUME_SENNA_ENV=1 only for the reviewed partial Senna environment.' >&2
    exit 1
  }
  [[ -f "$prefix/conda-meta/history" && -x "$prefix/bin/python" ]] || {
    echo 'Existing prefix is not a usable Conda environment; preserve it for diagnosis.' >&2; exit 1;
  }
  "$prefix/bin/python" - <<'PYTHON'
import importlib.metadata as metadata
import sys
assert sys.version_info[:2] == (3, 10), 'Resume requires the reviewed Python 3.10 prefix'
for package, expected in {'torch': '2.0.1+cu118', 'torchvision': '0.15.2+cu118', 'torchaudio': '2.0.2+cu118'}.items():
    actual = metadata.version(package)
    assert actual == expected, f'Resume refused: {package}={actual}, expected {expected}'
print('RESUME_VERIFIED: Python and torch package metadata match; no model/GPU claim')
PYTHON
  conda list --prefix "$prefix" --explicit
  "$prefix/bin/python" -m pip freeze --all
fi
"$python_bin" -m src.network_check
set -x
if [[ ! -e "$prefix" ]]; then
  # Explicit CLI channels are visible to Conda's pre-command hooks.
  conda create --yes --prefix "$prefix" --override-channels \
    --channel https://conda.anaconda.org/conda-forge --no-default-packages \
    python=3.10 pip
fi
"$python_bin" -m src.senna_requirements --upstream "$upstream/senna" --output "$profile"
# One resolution applies official runtime pins, including NumPy, before imports.
"$prefix/bin/python" -m pip install \
  --extra-index-url https://download.pytorch.org/whl/cu118 -r "$profile"
conda list --prefix "$prefix" --explicit
"$prefix/bin/python" scripts/environments/probe.py senna --packages-only --upstream "$upstream/senna"
