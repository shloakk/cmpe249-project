#!/usr/bin/env bash
#SBATCH --job-name=senna-audit
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=00:20:00
set -euo pipefail
: "${SLURM_JOB_ID:?Submit through sbatch}"
cd "${SLURM_SUBMIT_DIR:?}"
set -a
source .env
set +a
split="${SPLIT:-val}"
predictions="$EXPERIMENT_ROOT/outputs/senna/${split}.jsonl"
audit_dir="$EXPERIMENT_ROOT/outputs/audit/${split}"
"$EXPERIMENT_ROOT/environments/senna/bin/python" \
  -m src.error_audit.analyze --predictions "$predictions" \
  --output-dir "$audit_dir"
printf 'SENNA_AUDIT_OK output=%s\n' "$audit_dir/metrics.json"
