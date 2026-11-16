#!/usr/bin/env bash
#SBATCH --job-name=package-connectivity
#SBATCH --partition=gpuqs
#SBATCH --account=coe
#SBATCH --qos=normal
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH --time=00:03:00
set -euo pipefail
: "${SLURM_JOB_ID:?Submit through sbatch}"
cd "${SLURM_SUBMIT_DIR:?}"
set -a
source .env
set +a
printf 'UTC: '; date -u +%FT%TZ
printf 'Job: %s\nHost: ' "$SLURM_JOB_ID"; hostname
printf 'Commit: '; git rev-parse HEAD
printf 'Dirty status:\n'; git status --short
printf 'GPU assignment (unchanged): %s\n' "${CUDA_VISIBLE_DEVICES:-UNSET}"
printf 'Command: python3 -m src.config\n'
"${CMPE249_PYTHON:-python3}" -m src.config
printf 'Command: python3 -m src.network_check\n'
"${CMPE249_PYTHON:-python3}" -m src.network_check
