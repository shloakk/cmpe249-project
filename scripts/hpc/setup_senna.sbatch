#!/usr/bin/env bash
#SBATCH --job-name=senna-environment
#SBATCH --partition=gpuqs
#SBATCH --account=coe
#SBATCH --qos=normal
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
exec 9>"$CMPE249_ARTIFACT_ROOT/logs/.senna-setup.lock"
flock -n 9 || { echo 'Senna environment setup already active' >&2; exit 1; }
printf 'UTC: '; date -u +%FT%TZ
printf 'Job: %s\nHost: ' "$SLURM_JOB_ID"; hostname
printf 'Commit: '; git rev-parse HEAD
printf 'Dirty status:\n'; git status --short
printf 'GPU assignment: %s\n' "${CUDA_VISIBLE_DEVICES:-UNSET}"
nvidia-smi
printf 'Command: bash scripts/environments/setup_senna.sh\n'
bash scripts/environments/setup_senna.sh
