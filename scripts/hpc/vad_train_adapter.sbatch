#!/usr/bin/env bash
#SBATCH --job-name=vad-adapter
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=96G
#SBATCH --time=2-00:00:00
set -euo pipefail
: "${SLURM_JOB_ID:?Submit through sbatch}"
cd "${SLURM_SUBMIT_DIR:?}"
set -a
source .env
set +a
condition="${CONDITION:?Set CONDITION to c1, c2, or c3}"
case "$condition" in c1|c2|c3) ;; *) echo 'Invalid CONDITION' >&2; exit 2;; esac
run_id="${RUN_ID:-$SLURM_JOB_ID}"
vad_root="$EXPERIMENT_ROOT/upstream/vad"
vad_python="$EXPERIMENT_ROOT/environments/vad/bin/python"
config="${VAD_CONFIG:?Set VAD_CONFIG to the generated condition config}"
pretrained="${VAD_CHECKPOINT:?Set VAD_CHECKPOINT to released VAD Tiny stage-2 .pth}"
work_dir="$EXPERIMENT_ROOT/outputs/vad/$condition/$run_id/train"
run_root=$(dirname "$work_dir")
runtime="$run_root/runtime"
[[ ! -e "$work_dir" ]] || {
  echo "Refusing to overwrite an existing VAD training run: $work_dir" >&2
  exit 1
}
mkdir -p "$work_dir"
[[ -x "$vad_python" && -f "$config" && -f "$pretrained" ]]
export PYTHONDONTWRITEBYTECODE=1
export PYTHONNOUSERSITE=1
repo=$PWD
bash "$repo/scripts/prepare_vad_runtime.sh" \
  "$runtime" "$vad_root" "$EXPERIMENT_ROOT/vad_data"
cp -p "$config" "$run_root/config.py"
sha256sum "$config" "$pretrained" > "$run_root/inputs.sha256"
{
  printf 'utc='; date -u +%FT%TZ
  printf 'slurm_job_id=%s\n' "$SLURM_JOB_ID"
  printf 'host='; hostname
  printf 'repository_commit='; git rev-parse HEAD
  printf 'vad_commit='; git -C "$vad_root" rev-parse HEAD
  printf 'condition=%s\nrun_id=%s\n' "$condition" "$run_id"
  printf 'pretrained=%s\nconfig=%s\n' "$pretrained" "$config"
  printf 'cuda_visible_devices=%s\n' "${CUDA_VISIBLE_DEVICES:-UNSET}"
} > "$run_root/run_metadata.txt"
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv \
  > "$run_root/gpu.csv"
(
  cd "$runtime"
  env -u PYTHONHOME PYTHONPATH="$runtime:$vad_root" "$vad_python" \
    "$vad_root/tools/train.py" "$config" --work-dir "$work_dir" \
    --cfg-options "load_from=$pretrained"
)
printf 'VAD_ADAPTER_TRAIN_OK condition=%s run=%s output=%s\n' \
  "$condition" "$run_id" "$work_dir"
