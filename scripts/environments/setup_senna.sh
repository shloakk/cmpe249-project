#!/usr/bin/env bash
set -euo pipefail
: "${SLURM_JOB_ID:?Run environment setup through SLURM}"
python_bin=${CMPE249_PYTHON:-python3}
"$python_bin" -m src.config
export PYTHONDONTWRITEBYTECODE=1
# Metadata generation for deepspeed needs torch installed first.
export DS_BUILD_OPS=0
export PIP_CACHE_DIR="$CMPE249_ARTIFACT_ROOT/caches/pip"
export CONDA_PKGS_DIRS="$CMPE249_ARTIFACT_ROOT/caches/conda-pkgs"
export TMPDIR="$CMPE249_ARTIFACT_ROOT/tmp"
upstream="$CMPE249_ARTIFACT_ROOT/upstream"
prefix="$CMPE249_ARTIFACT_ROOT/environments/senna"
command -v conda
"$python_bin" -m src.upstream --root "$upstream" senna
if [[ -e "$prefix" ]]; then
  echo "Environment already exists: $prefix. Inspect prior logs; do not overwrite it." >&2
  exit 1
fi
set -x
conda env create --prefix "$prefix" --file environment-senna.yml
conda run --no-capture-output --prefix "$prefix" python -m pip install \
  --extra-index-url https://download.pytorch.org/whl/cu118 \
  torch==2.0.1+cu118 torchvision==0.15.2+cu118 torchaudio==2.0.2+cu118
conda run --no-capture-output --prefix "$prefix" python -m pip install \
  --extra-index-url https://download.pytorch.org/whl/cu118 -r "$upstream/senna/requirements.txt"
conda list --prefix "$prefix" --explicit
conda run --no-capture-output --prefix "$prefix" python scripts/environments/probe.py \
  senna --upstream "$upstream/senna"
