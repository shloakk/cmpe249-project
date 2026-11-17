#!/usr/bin/env bash
set -euo pipefail
repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
cd "$repo"
[[ -f .env ]] || { echo 'Create ignored .env first; see REPRODUCIBILITY.md' >&2; exit 1; }
set -a
source .env
set +a
# Only path checks and submission on login node; GPU probe runs inside SLURM.
"${HOST_PYTHON:-python3}" -m src.config
mkdir -p "$EXPERIMENT_ROOT/logs"
printf 'Command: sbatch --parsable --chdir=%q --output=%q --error=%q scripts/hpc/smoke.sbatch\n' \
  "$repo" "$EXPERIMENT_ROOT/logs/smoke-%j.out" "$EXPERIMENT_ROOT/logs/smoke-%j.err"
sbatch --parsable --chdir="$repo" \
  --output="$EXPERIMENT_ROOT/logs/smoke-%j.out" \
  --error="$EXPERIMENT_ROOT/logs/smoke-%j.err" scripts/hpc/smoke.sbatch
