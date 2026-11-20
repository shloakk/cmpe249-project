#!/usr/bin/env bash
#SBATCH --job-name=vad-eval
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=12:00:00
set -euo pipefail
: "${SLURM_JOB_ID:?Submit through sbatch}"
cd "${SLURM_SUBMIT_DIR:?}"
set -a
source .env
set +a
condition="${CONDITION:-c0}"
run_id="${RUN_ID:-$SLURM_JOB_ID}"
vad_root="$EXPERIMENT_ROOT/upstream/vad"
vad_python="$EXPERIMENT_ROOT/environments/vad/bin/python"
checkpoint="${VAD_CHECKPOINT:?Set VAD_CHECKPOINT to the released VAD Tiny stage-2 .pth}"
config="${VAD_CONFIG:-$vad_root/projects/configs/VAD/VAD_tiny_stage_2.py}"
result="$EXPERIMENT_ROOT/outputs/vad/$condition/$run_id"
runtime="$result/runtime"
mkdir -p "$result"
[[ -x "$vad_python" && -f "$checkpoint" && -f "$config" ]]
[[ ! -e "$result/predictions.pkl" && ! -e "$result/planning_metrics.json" ]] || {
  echo "Refusing to overwrite an existing VAD run: $result" >&2
  exit 1
}
export PYTHONDONTWRITEBYTECODE=1
export PYTHONNOUSERSITE=1
repo=$PWD
bash "$repo/scripts/prepare_vad_runtime.sh" \
  "$runtime" "$vad_root" "$EXPERIMENT_ROOT/vad_data"
cp -p "$config" "$result/config.py"
sha256sum "$config" "$checkpoint" > "$result/inputs.sha256"
{
  printf 'utc='; date -u +%FT%TZ
  printf 'slurm_job_id=%s\n' "$SLURM_JOB_ID"
  printf 'host='; hostname
  printf 'repository_commit='; git rev-parse HEAD
  printf 'vad_commit='; git -C "$vad_root" rev-parse HEAD
  printf 'condition=%s\nrun_id=%s\n' "$condition" "$run_id"
  printf 'checkpoint=%s\nconfig=%s\n' "$checkpoint" "$config"
  printf 'cuda_visible_devices=%s\n' "${CUDA_VISIBLE_DEVICES:-UNSET}"
} > "$result/run_metadata.txt"
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv \
  > "$result/gpu.csv"
(
  cd "$runtime"
  env -u PYTHONHOME PYTHONPATH="$runtime:$vad_root" "$vad_python" \
    "$vad_root/tools/test.py" "$config" "$checkpoint" \
    --out "$result/predictions.pkl"
)
env -u PYTHONPATH -u PYTHONHOME "$vad_python" \
  "$repo/src/vad_metrics.py" --input "$result/predictions.pkl" \
  --output "$result/planning_metrics.json"
printf 'VAD_EVAL_OK condition=%s run=%s output=%s\n' \
  "$condition" "$run_id" "$result"
