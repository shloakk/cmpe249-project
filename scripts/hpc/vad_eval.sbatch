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
vad_root="$EXPERIMENT_ROOT/upstream/vad"
image="$EXPERIMENT_ROOT/environments/vad.sif"
checkpoint="${VAD_CHECKPOINT:?Set VAD_CHECKPOINT to the released VAD Tiny stage-2 .pth}"
config="${VAD_CONFIG:-$vad_root/projects/configs/VAD/VAD_tiny_stage_2.py}"
result="$EXPERIMENT_ROOT/outputs/vad/$condition"
mkdir -p "$result"
[[ -f "$image" && -f "$checkpoint" && -f "$config" ]]
bind="$PWD:$PWD,$NUSCENES_DATA_ROOT:$NUSCENES_DATA_ROOT,$NUSCENES_DERIVED_ROOT:$NUSCENES_DERIVED_ROOT,$EXPERIMENT_ROOT:$EXPERIMENT_ROOT"
env -u PYTHONPATH -u PYTHONHOME apptainer exec --nv --bind "$bind" "$image" \
  bash -lc "cd '$vad_root' && python3 tools/test.py '$config' '$checkpoint' \
    --out '$result/predictions.pkl'"
env -u PYTHONPATH -u PYTHONHOME apptainer exec --bind "$bind" "$image" \
  python3 "$PWD/src/vad_metrics.py" --input "$result/predictions.pkl" \
  --output "$result/planning_metrics.json"
printf 'VAD_EVAL_OK condition=%s output=%s\n' "$condition" "$result"
