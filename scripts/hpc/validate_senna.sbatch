#!/usr/bin/env bash
#SBATCH --job-name=senna-validation
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=00:10:00
set -euo pipefail
: "${SLURM_JOB_ID:?Submit through sbatch}"
cd "${SLURM_SUBMIT_DIR:?}"
set -a
source .env
set +a
"${HOST_PYTHON:-python3}" -m src.config
export PYTHONDONTWRITEBYTECODE=1
exec 9>"$EXPERIMENT_ROOT/logs/.senna-setup.lock"
flock -n 9 || { echo 'Senna installation or validation already active' >&2; exit 1; }
printf 'UTC: '; date -u +%FT%TZ
printf 'Job: %s\nHost: ' "$SLURM_JOB_ID"; hostname
printf 'Commit: '; git rev-parse HEAD
printf 'Dirty status:\n'; git status --short
printf 'GPU assignment: %s\n' "${CUDA_VISIBLE_DEVICES:-UNSET}"
nvidia-smi
printf 'Command: verify pinned Senna source, then run import/CUDA probe\n'
"${HOST_PYTHON:-python3}" -m src.upstream --root "$EXPERIMENT_ROOT/upstream" --verify-only senna
"$EXPERIMENT_ROOT/environments/senna/bin/python" scripts/environments/probe.py \
  senna --upstream "$EXPERIMENT_ROOT/upstream/senna"
