#!/usr/bin/env bash
set -euo pipefail
repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
cd "$repo"
[[ -f .env ]] || { echo 'Create ignored .env first; see REPRODUCIBILITY.md' >&2; exit 1; }
set -a
source .env
set +a
# Only path checks and submission on login node; GPU probe runs inside SLURM.
"${CMPE249_PYTHON:-python3}" -m src.config
mkdir -p "$CMPE249_ARTIFACT_ROOT/logs"
printf 'Command: sbatch --parsable --chdir=%q --output=%q --error=%q scripts/hpc/smoke.sbatch\n' \
  "$repo" "$CMPE249_ARTIFACT_ROOT/logs/smoke-%j.out" "$CMPE249_ARTIFACT_ROOT/logs/smoke-%j.err"
sbatch --parsable --chdir="$repo" \
  --output="$CMPE249_ARTIFACT_ROOT/logs/smoke-%j.out" \
  --error="$CMPE249_ARTIFACT_ROOT/logs/smoke-%j.err" scripts/hpc/smoke.sbatch
