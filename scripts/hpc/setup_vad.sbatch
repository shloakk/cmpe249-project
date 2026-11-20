#!/usr/bin/env bash
#SBATCH --job-name=vad-validation
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=02:00:00
set -euo pipefail
: "${SLURM_JOB_ID:?Submit through sbatch}"
cd "${SLURM_SUBMIT_DIR:?}"
set -a
source .env
set +a
"${HOST_PYTHON:-python3}" -m src.config
exec 9>"$EXPERIMENT_ROOT/logs/.vad-setup.lock"
flock -n 9 || { echo 'VAD environment setup already active' >&2; exit 1; }
printf 'UTC: '; date -u +%FT%TZ
printf 'Job: %s\nHost: ' "$SLURM_JOB_ID"; hostname
printf 'Commit: '; git rev-parse HEAD
printf 'Dirty status:\n'; git status --short
printf 'GPU assignment: %s\n' "${CUDA_VISIBLE_DEVICES:-UNSET}"
nvidia-smi
export PYTHONDONTWRITEBYTECODE=1
export PYTHONNOUSERSITE=1
vad_python="$EXPERIMENT_ROOT/environments/vad/bin/python"
vad_root="$EXPERIMENT_ROOT/upstream/vad"
[[ -x "$vad_python" ]] || {
  echo "Missing VAD Python environment: $vad_python" >&2
  exit 1
}
set -x
"${HOST_PYTHON:-python3}" -m src.upstream --root "$EXPERIMENT_ROOT/upstream" --verify-only vad
env -u PYTHONPATH -u PYTHONHOME "$vad_python" \
  scripts/environments/probe.py vad --upstream "$vad_root"
