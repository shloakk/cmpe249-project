#!/usr/bin/env bash
#SBATCH --job-name=senna-cache
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=64G
#SBATCH --time=12:00:00
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
: "${SLURM_JOB_ID:?Submit through sbatch}"
cd "${SLURM_SUBMIT_DIR:?}"
set -a
source .env
set +a
python_bin="$EXPERIMENT_ROOT/environments/senna/bin/python"
senna_root="$EXPERIMENT_ROOT/upstream/senna"
checkpoint="${SENNA_MODEL_PATH:-$SENNA_CHECKPOINT_ROOT/Senna}"
split="${SPLIT:-val}"
preferred="$EXPERIMENT_ROOT/vad_data/vad_nuscenes_infos_temporal_${split}.pkl"
fallback="$NUSCENES_DERIVED_ROOT/nuscenes_infos_${split}.pkl"
if [[ -n "${ANNOTATION:-}" ]]; then
  annotation="$ANNOTATION"
elif [[ -f "$preferred" ]]; then
  annotation="$preferred"
else
  annotation="$fallback"
fi
manifest="$EXPERIMENT_ROOT/caches/manifests/${split}.json"
predictions="$EXPERIMENT_ROOT/outputs/senna/${split}.jsonl"
mkdir -p "$(dirname "$manifest")" "$(dirname "$predictions")" \
  "$EXPERIMENT_ROOT/logs"
"$python_bin" -m src.config
"$python_bin" -m src.upstream --root "$EXPERIMENT_ROOT/upstream" \
  --verify-only senna
printf 'Job=%s host=%s commit=%s GPU=%s\n' "$SLURM_JOB_ID" "$(hostname)" \
  "$(git rev-parse HEAD)" "${CUDA_VISIBLE_DEVICES:-UNSET}"
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv
if [[ ! -s "$manifest" ]]; then
  "$python_bin" -m src.senna_cache.build_manifest \
    --annotation "$annotation" --data-root "$NUSCENES_DATA_ROOT" \
    --output "$manifest"
fi
"$python_bin" -m src.senna_cache.run_inference \
  --manifest "$manifest" --output "$predictions" \
  --senna-root "$senna_root" --checkpoint "$checkpoint" \
  --limit "${LIMIT:-0}" --max-new-tokens "${MAX_NEW_TOKENS:-64}"
printf 'SENNA_CACHE_OK predictions=%s lines=' "$predictions"
wc -l < "$predictions"
