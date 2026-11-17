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
vad_root="$EXPERIMENT_ROOT/upstream/vad"
image="$EXPERIMENT_ROOT/environments/vad.sif"
config="${VAD_CONFIG:?Set VAD_CONFIG to the generated condition config}"
pretrained="${VAD_CHECKPOINT:?Set VAD_CHECKPOINT to released VAD Tiny stage-2 .pth}"
work_dir="$EXPERIMENT_ROOT/outputs/vad/$condition/train"
mkdir -p "$work_dir"
[[ -f "$image" && -f "$config" && -f "$pretrained" ]]
bind="$PWD:$PWD,$NUSCENES_DATA_ROOT:$NUSCENES_DATA_ROOT,$NUSCENES_DERIVED_ROOT:$NUSCENES_DERIVED_ROOT,$EXPERIMENT_ROOT:$EXPERIMENT_ROOT"
env -u PYTHONPATH -u PYTHONHOME apptainer exec --nv --bind "$bind" "$image" \
  bash -lc "cd '$vad_root' && python3 tools/train.py '$config' \
    --work-dir '$work_dir' --cfg-options load_from='$pretrained'"
printf 'VAD_ADAPTER_TRAIN_OK condition=%s output=%s\n' "$condition" "$work_dir"
